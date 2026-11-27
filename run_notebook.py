"""Rebuild the notebook using the Python environment running this script."""
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager


def main():
    path = Path(__file__).resolve().parent / 'notebook' / 'Team05_Analysis.ipynb'
    notebook = nbformat.read(path, as_version=4)
    manager = KernelManager(kernel_name='python3')
    manager.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
    client = NotebookClient(notebook, km=manager, timeout=300, allow_errors=False,
                            resources={'metadata': {'path': str(path.parent)}})
    client.execute()
    nbformat.write(notebook, path)
    print('Notebook completed. Cleaned data, results and figures have been rebuilt.')


if __name__ == '__main__':
    main()
