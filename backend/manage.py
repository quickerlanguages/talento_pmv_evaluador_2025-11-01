
#!/usr/bin/env python3
import os, sys
def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talento_backend_v2.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
if __name__ == '__main__':
    main()
