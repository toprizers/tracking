import sys
import os


def get_persistent_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def main():
    persistent_config = os.path.join(get_persistent_dir(), 'config.json')

    if '--setup' in sys.argv or not os.path.exists(persistent_config):
        from setup_gui import SetupGUI
        app = SetupGUI()
        app.run()
    else:
        from main import MonitorAgent
        import signal

        agent = MonitorAgent(persistent_config)

        def signal_handler(sig, frame):
            agent.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        agent.run()


if __name__ == '__main__':
    main()
