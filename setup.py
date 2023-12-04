from setuptools import setup, find_packages
# List of requirements
requirements = "requirements.txt"  # This could be retrieved from requirements.txt
# Package (minimal) configuration
setup(
    name="eartools",
    version="1.0.0",
    description="eartools",
    packages=find_packages(),  # __init__.py folders search
    install_requires=['fastapi==0.104.1',
        'ipython>=8.16.1',
        'kivymd>=1.1.1',
        'matplotlib>=3.8.0',
        'numpy>=1.26.1',
        'pandas>=2.1.2',
        'Requests>=2.31.0',
        'scikit_learn>=1.3.1',
        'speechbrain>=0.5.15',
        'torch>=2.1.0',
        'torchaudio>=2.1.0',
        'tqdm>=4.66.1']
)
