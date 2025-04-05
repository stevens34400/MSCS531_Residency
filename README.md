# Gem5 Repository - MSCS 531 Group Project

## Project Overview
This repository contains the work for **Spring 2025, Group Project - 3** as part of the **MSCS - 531 Computer Architecture and Design** course at the University of the Cumberlands. The project focuses on defining and designing a computer architecture using the Gem5 simulator.

### Course Details
- **Course**: MSCS - 531 Computer Architecture and Design
- **Instructor**: Dr. Garry Perry  
- **Institution**: University of the Cumberlands  

### Team Members
- Amit Yadav  
- Sushil Khanal  
- Mohit Gokul Murali  
- Steven Sisjayawan  

## Prerequisites
To build and run the Gem5 simulator in this repository, ensure you have the following installed:
- **Operating System**: Linux (Ubuntu recommended) or macOS
- **Dependencies**:
  - GCC (version 7 or higher)
  - Python (version 3.6 or higher)
  - SCons (build tool)
  - Git
  - Other Gem5 dependencies (e.g., zlib, m4, etc.)

Install the required dependencies on Ubuntu with:
```bash
sudo apt-get update
sudo apt-get install build-essential git m4 scons zlib1g zlib1g-dev libprotobuf-dev protobuf-compiler libprotoc-dev libgoogle-perftools-dev python3-dev python3-six python-is-python3
```
To set up the project:

1. Clone the Repository:
     ```
     git clone <repository-url>
     cd gem5
     ```
2. Build Gem5:
Use the SCons build system to compile Gem5 with the X86 architecture optimized configuration:
  ```
  scons build/X86/gem5.opt -j$(nproc)
  build/X86/gem5.opt: Builds the optimized version of Gem5 for the X86 architecture.
-j$(nproc): Uses all available CPU cores to speed up the build process.
```
3. Running a Sample Configuration
To run a sample simulation using the provided configuration file:

  ```
  build/X86/gem5.opt configs/deprecated/example/x86_atom_config_32_optimized.py
  ```
