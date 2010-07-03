from setuptools import setup, find_packages


VERSION = __import__('openscriptures_texts').__version__

setup (
    name='openscriptures_texts',
    version = VERSION,
    author='Weston Ruter',
    author_email='weston@somewhere.org',
    url='git@github.com/openscriptures/openscriptures_texts.git',
    description="""The OpenScriptures API""",
    packages=find_packages(),
    namespace_packages = [],
    include_package_data = True,
    zip_safe=False,
    license='MIT/GPL',
    install_requires=["Django", ]
)
