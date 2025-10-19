# 🚀 Hyperway v1.0.0 - Production Ready!

A functional graph execution engine that makes computational graphs clean, composable, and fun to work with.

---

## 🎯 What's New in 1.0.0

### Code Quality & Maintainability
- **Systematic DRY refactoring** across test suite (-265 lines)
- **Factory pattern helpers** (`add_n`, `return_n`) replace 20+ duplicate functions
- **Introduced tiny_tools module** for shared test utilities
- **Meta-testing innovation** for comprehensive edge case coverage

### Test Suite Excellence
- **309 tests passing** with robust assertions
- **100% coverage achievement** (3,017/3,017 statements)
- All source and test files fully covered
- Cleaner, more maintainable test code

### Enhanced Documentation
- Updated project descriptions for clarity
- Production/Stable development status
- Comprehensive metadata in pyproject.toml
- Better classifiers and package information

### Version Evolution
- **Bumped from 0.2 → 1.0.0**
- Marks production-ready maturity
- Stable API and behavior guarantees

---

## ✨ Core Features

### Graph Execution
- **Left-associative edge execution** (A → [wire] → B)
- `Connection.pluck()` for complete edge traversal
- Stepper-based execution with branch management
- Row stashing for end-node result collection

### Node Capabilities
- **Merge nodes** for multi-input aggregation
- **Sentinel-based value flow** control
- Unit wrapper with automatic callable handling
- Support for instance methods as nodes

### Data Flow
- **ArgsPack** for clean inter-node communication
- Wire functions for edge transformations
- Automatic args/kwargs propagation
- Type-safe value passing

### Visualization
- **Graphviz rendering** support
- Customizable graph layouts (LR, TB, etc.)
- Visual debugging of graph topology

---

## 📦 Package Info

- **Python**: >=3.8
- **License**: MIT
- **Status**: Production/Stable
- **Install**: `pip install hyperway`

---

Built with functional programming principles and dedication to code quality. Ready for production use! 🎉
