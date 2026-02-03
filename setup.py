from setuptools import setup, find_packages

setup(
    name="frappe_devops_monitor",
    version="1.0.0",
    description="Comprehensive DevOps Monitoring App for Frappe Framework",
    author="DevOps Team",
    author_email="devops@example.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        "psutil>=5.9.0",
    ],
)
