from conjure.api.models import model_info, model_cache_controller_provider
from conjure.charm import get_bundle
from conjure.models.bundle import BundleModel

from bundleplacer.config import Config
from bundleplacer.maas import connect_to_maas
from bundleplacer.placerview import PlacerView
from bundleplacer.controller import PlacementController, BundleWriter
from urllib.parse import urlparse


class DeployController:

    def __init__(self, app, controller):
        self.app = app
        self.controller_info = model_info(controller)
        self.placement_controller = None
        self.bundle = None

    def finish(self, *args):
        """ handles deployment
        """
        bw = BundleWriter(self.placement_controller)
        bw.write_bundle(self.bundle)
        self.app.controllers['deploysummary'](self.app, self.bundle).render()

    def render(self):
        # Grab bundle and deploy or render placement if MAAS
        self.bundle = get_bundle(BundleModel.to_entity(), to_file=True)
        metadata_filename = self.app.config['metadata_filename']

        bundleplacer_cfg = Config(
            'bundle-placer',
            {'bundle_filename': self.bundle,
             'metadata_filename': metadata_filename})

        if self.controller_info['ProviderType'] == 'maas':
            bootstrap_config = model_cache_controller_provider(
                self.controller_info['ServerUUID'])
            maas_server = urlparse(bootstrap_config['maas-server'])
            creds = dict(
                api_host=maas_server.hostname,
                api_key=bootstrap_config['maas-oauth'])
            maas, maas_state = connect_to_maas(creds)
            self.placement_controller = PlacementController(
                config=bundleplacer_cfg,
                maas_state=maas_state)
            mainview = PlacerView(self.placement_controller,
                                  bundleplacer_cfg,
                                  self.finish, has_maas=True)
            self.app.ui.set_header(
                title=self.app.config['summary'],
                excerpt=("Place services, add additional charms, and manage "
                         "service relations")
            )
            self.app.ui.set_subheader("Bundle Editor")
            self.app.ui.set_body(mainview)
            mainview.update()
        else:
            self.placement_controller = PlacementController(
                config=bundleplacer_cfg)
            mainview = PlacerView(self.placement_controller,
                                  bundleplacer_cfg,
                                  self.finish)
            self.app.ui.set_header(
                title=self.app.config['summary'],
                excerpt=("Add additional charms and manage service relations")
            )
            self.app.ui.set_subheader("Bundle Editor")
            self.app.ui.set_body(mainview)
            mainview.update()
