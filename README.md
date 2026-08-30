# AI-Powered DevOps Debugging Agent

An LLM-powered DevOps debugging agent that automatically analyzes application and Docker runtime failures, uses tool calling to inspect and modify project files, validates proposed fixes, and iteratively reruns the application and tests until the issue is resolved.

## 🚀 Overview

Debugging application failures often requires repeatedly:

1. Inspecting the project
2. Running the application
3. Reading the error
4. Finding the problematic code
5. Modifying the code
6. Running the application again
7. Running tests
8. Verifying that the fix actually works

This project automates that debugging workflow using an LLM-based agent.

The agent doesn't simply generate a suggested fix. It can interact with the project through tools, observe the results, reason about failures, and continue the debugging cycle.

## 🧠 Architecture

```text
                    ┌─────────────────────┐
                    │     User Project     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Project Scanner   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Project Runner   │
                    └──────────┬──────────┘
                               │
                         Error / Output
                               │
                               ▼
                    ┌─────────────────────┐
                    │    LLM Debugger     │
                    │    LLaMA 3.2        │
                    └──────────┬──────────┘
                               │
                         Tool Calling
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        Read Files       Modify Files      Run Commands
              │                │                │
              └────────────────┼────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Validate Patch    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Run Application   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Run Tests       │
                    └──────────┬──────────┘
                               │
                               ▼
                       Tests Passed?
                         /         \
                       Yes          No
                       │             │
                       ▼             │
                     Done ◄──────────┘
                             
                         Debug Again
````

## ✨ Features

* Automatic project scanning
* Application execution and output capture
* Error and failure analysis using an LLM
* Agentic tool calling
* File inspection
* Code modification
* Command execution
* Automated patch validation
* Python syntax validation
* Docker runtime failure detection
* Pytest integration
* Iterative debugging and verification
* Configurable maximum debugging attempts

## 🔧 Tool Calling

The agent interacts with the project through specialized tools instead of directly manipulating the environment.

Current tools include:

### File Tools

* `read_file` — reads project files
* `modify_file` — applies validated code modifications

### Command Tools

* `run_command` — executes shell commands

### Test Tools

* `run_tests` — executes the project's test suite

### Project Tools

* Project scanning
* Application execution
* Project validation

The LLM decides when a tool is required based on the current debugging state.

## 🔄 Debugging Loop

The core workflow is:

```text
Scan Project
     ↓
Run Application
     ↓
Capture Failure
     ↓
Analyze Failure
     ↓
LLM Selects Required Tool
     ↓
Inspect / Modify / Execute
     ↓
Validate Proposed Fix
     ↓
Run Application Again
     ↓
Run Tests
     ↓
Tests Pass?
   ↙       ↘
 Yes        No
  ↓          ↓
 Done    Analyze Again
```

The important part is that the agent **verifies its own proposed fix** instead of assuming that generated code is correct.

## 🐳 Docker Debugging

The agent also supports debugging failures that occur during Docker execution.

For example:

```dockerfile
CMD ["python", "wrong.py"]
```

can produce a Docker runtime failure.

The agent can identify the failure category, inspect the Dockerfile, propose the minimal correction, validate the change, and rerun the container.

## 🧪 Example

Given a project containing:

```text
test_project/
├── app.py
├── Dockerfile
├── requirements.txt
├── .dockerignore
└── tests/
    ├── __init__.py
    └── test_app.py
```

The agent can:

```text
$ python3 agent.py test_project
```

Then:

```text
Project scanned
      ↓
Application executed
      ↓
Runtime failure detected
      ↓
LLM analyzes traceback
      ↓
Relevant file inspected
      ↓
Fix proposed
      ↓
Patch validated
      ↓
Application rerun
      ↓
Pytest executed
      ↓
Tests passed
```

## 🛠️ Tech Stack

* Python
* LLaMA 3.2
* Ollama
* Docker
* Pytest
* Git
* Abstract Syntax Tree (`ast`)
* LLM-based Agentic Workflow
* Tool Calling

## 📁 Project Structure

```text
devops-debugging-agent/
│
├── agent.py
│
├── core/
│   └── validator.py
│
├── project/
│   ├── scanner.py
│   └── runner.py
│
├── tools/
│   ├── file_tools.py
│   ├── command_tools.py
│   ├── test_tools.py
│   └── git_tools.py
│
├── prompts/
│   └── debug_prompts.py
│
└── test_project/
    ├── app.py
    ├── Dockerfile
    ├── requirements.txt
    ├── .dockerignore
    └── tests/
```

## ▶️ Running the Agent

Clone the repository:

```bash
git clone <repository-url>
cd devops-debugging-agent
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Make sure Ollama is installed and the required model is available.

Then run:

```bash
python3 agent.py <project_path>
```

Example:

```bash
python3 agent.py test_project
```

## 🎯 Project Goal

The long-term goal is to build an autonomous debugging system capable of:

* Detecting application failures
* Understanding runtime and test failures
* Selecting appropriate debugging tools
* Generating minimal fixes
* Validating modifications
* Verifying fixes through execution and testing
* Iterating until the project reaches a successful state

## 🚧 Current Status

### Implemented

* [x] Project scanning
* [x] Application execution
* [x] Error capture
* [x] LLM-based failure analysis
* [x] Tool-based file inspection
* [x] Code modification
* [x] Patch validation
* [x] Python syntax validation
* [x] Automated test execution
* [x] Iterative debugging loop
* [x] Docker runtime debugging

### Planned

* [ ] Improved multi-language support
* [ ] CI/CD integration
* [ ] Jenkins integration
* [ ] Retrieval-Augmented Generation (RAG)
* [ ] Better patch verification
* [ ] Human approval workflow
* [ ] Expanded debugging tools

```

### One important thing

**Don't put features under “Implemented” until we've actually built them.**

For example, if we haven't implemented Jenkins, RAG, human approval, etc., leave them under **Planned**.

That's actually a good practice for this project because it makes the README show the **evolution of the agent**, rather than making it look like you built everything at once.

And once we finish the current version, we should add a **real example run with your actual terminal output**. That will make the README considerably stronger than a generic description.
```
