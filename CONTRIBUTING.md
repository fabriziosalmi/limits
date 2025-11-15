# Contributing to Limits

Thank you for your interest in contributing to the Limits project! We welcome contributions from the community and appreciate your help in making this project better.

## Table of Contents

*   [Code of Conduct](#code-of-conduct)
*   [Getting Started](#getting-started)
*   [How to Contribute](#how-to-contribute)
*   [Coding Guidelines](#coding-guidelines)
*   [Testing Guidelines](#testing-guidelines)
*   [Submitting a Pull Request](#submitting-a-pull-request)
*   [Reporting Issues](#reporting-issues)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please be respectful and considerate in your interactions with other contributors.

## Getting Started

1.  **Fork the Repository:**
    Click the "Fork" button at the top right of the [repository page](https://github.com/fabriziosalmi/limits).

2.  **Clone Your Fork:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/limits.git
    cd limits
    ```

3.  **Set Up the Development Environment:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a Feature Branch:**
    ```bash
    git checkout -b feature/your-feature-name
    ```

## How to Contribute

There are many ways to contribute:

*   **Report Bugs:** If you find a bug, please open an issue with detailed information.
*   **Suggest Enhancements:** Have an idea for a new feature? Open an issue to discuss it.
*   **Improve Documentation:** Help us make the documentation clearer and more comprehensive.
*   **Submit Code:** Fix bugs, add features, or improve existing code.

## Coding Guidelines

*   **Follow PEP 8:** Python code should follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines.
*   **Use Type Hints:** Add type hints to function signatures for better code clarity.
*   **Write Clear Comments:** Comment complex logic to help others understand your code.
*   **Keep It Simple:** Write clean, readable code. Avoid unnecessary complexity.
*   **Use Meaningful Names:** Use descriptive variable and function names.

### Code Style Examples

```python
# Good
def calculate_rate_limit(requests_per_minute: int, window: str) -> dict:
    """
    Calculate rate limit configuration.
    
    Args:
        requests_per_minute: Number of allowed requests per minute
        window: Time window for rate limiting (e.g., '1m', '5s')
    
    Returns:
        Dictionary containing rate limit configuration
    """
    return {
        'rate': requests_per_minute,
        'window': window
    }

# Bad
def calc(rpm, w):
    return {'rate': rpm, 'window': w}
```

## Testing Guidelines

*   **Test Your Changes:** Before submitting a pull request, ensure your changes work correctly.
*   **Run All Scripts:** Test that all conversion scripts execute without errors:
    ```bash
    python ratelimit.py
    python ratelimit2nginx.py
    python ratelimit2apache.py
    python ratelimit2traefik.py
    python ratelimit2haproxy.py
    ```
*   **Validate Generated Configurations:** Check that the generated configuration files are syntactically correct for their respective web servers.
*   **Test Edge Cases:** Consider edge cases and unusual inputs.

## Submitting a Pull Request

1.  **Make Your Changes:**
    Implement your feature or bug fix on your feature branch.

2.  **Commit Your Changes:**
    Write clear, concise commit messages following conventional commit format:
    ```bash
    git add .
    git commit -m "feat: add support for custom headers"
    # or
    git commit -m "fix: correct nginx rate limit syntax"
    # or
    git commit -m "docs: update README with new examples"
    ```

    **Commit Message Prefixes:**
    *   `feat:` - New feature
    *   `fix:` - Bug fix
    *   `docs:` - Documentation changes
    *   `style:` - Code style changes (formatting, etc.)
    *   `refactor:` - Code refactoring
    *   `test:` - Adding or updating tests
    *   `chore:` - Maintenance tasks

3.  **Push to Your Fork:**
    ```bash
    git push origin feature/your-feature-name
    ```

4.  **Open a Pull Request:**
    *   Go to the [original repository](https://github.com/fabriziosalmi/limits).
    *   Click "New Pull Request".
    *   Select your fork and branch.
    *   Fill in the PR template with:
        *   **Title:** A clear, descriptive title
        *   **Description:** What changes you made and why
        *   **Related Issues:** Reference any related issues (e.g., "Fixes #123")
        *   **Testing:** How you tested your changes

5.  **Review Process:**
    *   A maintainer will review your PR.
    *   Address any feedback or requested changes.
    *   Once approved, your PR will be merged.

## Reporting Issues

When reporting an issue, please include:

*   **Description:** A clear description of the problem
*   **Steps to Reproduce:** Detailed steps to reproduce the issue
*   **Expected Behavior:** What you expected to happen
*   **Actual Behavior:** What actually happened
*   **Environment:**
    *   Operating System
    *   Python version
    *   Web server and version (if applicable)
*   **Configuration:** Relevant parts of your `config.yaml` (sanitize any sensitive data)
*   **Error Messages:** Full error messages or stack traces

## Questions?

If you have questions about contributing, feel free to:

*   Open an issue with the `question` label
*   Reach out to the maintainers

Thank you for contributing to Limits! 🎉
