# Graphviz Installation Guide

This document provides installation instructions for Graphviz 14.0.1 on different operating systems.

## Linux (Debian/Ubuntu)

The apt install didn't work for me, so performing the steps manually from their GitLab repo:

Download the Debian package:

```bash
wget https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/14.0.1/ubuntu_25.04_graphviz-14.0.1-cmake.deb -O /tmp/graphviz-14.0.1.deb
```

Install: 

```bash
sudo dpkg -i /tmp/graphviz-14.0.1.deb
```

Verify: 

```bash
dot -V
```

## Additional Resources

- Official Graphviz Website: https://graphviz.org/
- GitLab Repository: https://gitlab.com/graphviz/graphviz
- Documentation: https://graphviz.org/documentation/
- Package Releases: https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/
