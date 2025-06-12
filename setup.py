from setuptools import setup, find_packages

setup(
    name="course-registration-validator",
    version="0.3.0",
    py_modules=["integrated_solution", "app", "validator", "transcript_editor_app", "batch_processor"],
    packages=find_packages(),
    package_data={
        "": ["*.json"],
    },
    include_package_data=True,
    install_requires=[
        "PyPDF2>=2.0.0",
        "appdirs>=1.4.4",
    ],
    entry_points={
        'console_scripts': [
            'course-validator=integrated_solution:main',
            'course-validator-batch=batch_processor:main',
        ],
    },
    python_requires='>=3.8',
    author="Modern Research Group",
    description="A system for validating course registrations against prerequisites",
    url="https://github.com/Modern-research-group/course-registration-validator",
)
