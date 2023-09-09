from vlc_server import run_vlc_server
import yaml

def validate_sections(cfg, sections):
    for sec in sections:
        if(not sec in cfg):
            print(f"Config section missing: {sec}")
            quit()

def validate_settings(cfg, section, settings):
    for entry in settings:
        if(not entry in cfg[section]):
            print(f"Config entry '{entry}' missing in section: {section}")
            quit()

def load_config():
    with open('config.yaml') as cfg_file:
        cfg = yaml.safe_load(cfg_file)

    # Trivial config validation
    validate_sections(cfg, ['server', 'audio'])
    validate_settings(cfg, 'server', ['port', 'password', 'allow_list'])
    validate_settings(cfg, 'audio', ['volume_device'])
    return cfg

if __name__ == "__main__":
    cfg = load_config()
    run_vlc_server(cfg)
