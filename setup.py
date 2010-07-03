from setuptools import setup, find_packages


setup (
    name='openscriptures_texts',
    version = '0.0.1',
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
