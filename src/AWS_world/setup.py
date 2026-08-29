from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'AWS_world'  # Lowercase recommended

def generate_data_files(share_path, dir_path):
    """Recursively collects all files in dir_path and maps them to install destinations."""
    data_files = []
    for root, _, files in os.walk(dir_path):
        if files:
            install_dir = os.path.join(share_path, root)
            file_paths = [os.path.join(root, f) for f in files]
            data_files.append((install_dir, file_paths))
    return data_files

data_files = [
    ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    (os.path.join('share',package_name,'launch'), glob("launch/*"))
]

# Add directory trees safely
for folder in ['worlds', 'models', 'maps']:
    if os.path.isdir(folder):
        data_files.extend(generate_data_files(os.path.join('share', package_name), folder))

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=data_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='vatsalya',
    maintainer_email='vatsalyabrahamtamj2@gmail.com',
    description='Package for simulation worlds and models',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [],
    },
)