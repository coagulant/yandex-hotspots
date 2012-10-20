from distutils.core import setup


setup(
    name='yandex-hotspots',
    version='0.1',
    py_modules=['hotspots'],
    url='https://github.com/coagulant/yandex-hotspots',
    requires=['Pillow (== 1.7.7)'],
    license='MIT',
    author='coagulant',
    author_email='baryshev@gmail.com',
    description='Generator of tiles and js for Yandex Maps Hotspots v2',
    long_description=open('README.rst').read()
)
