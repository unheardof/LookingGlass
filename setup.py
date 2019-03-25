import setuptools

with open("README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name="looking_glass",
	version="1.0.3",
	author="Timothy Heard",
	description="Web-based tool for visualizing data from network scanning and reconnaissance tools",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/unheardof/LookingGlass",
	packages=setuptools.find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: Apache Software License",
		"Operating System :: OS Independent",
		"Environment :: Console",
	],
	include_package_data=True,
)
