# Django Template Guidelines and Best Practices

## Table of Contents

1. [Template Syntax Rules](#template-syntax-rules)
2. [Common Issues and Solutions](#common-issues-and-solutions)
3. [Best Practices](#best-practices)
4. [Template Structure](#template-structure)
5. [Performance Considerations](#performance-considerations)
6. [Security Guidelines](#security-guidelines)
7. [Accessibility Guidelines](#accessibility-guidelines)
8. [Validation Tools](#validation-tools)

## Template Syntax Rules

### 1. Template Tag Formatting

#### ✅ Correct Formatting

```django
{% if user.is_authenticated %}
    <p>Welcome, {{ user.username }}!</p>
{% endif %}
```

#### ❌ Incorrect Formatting

```django
<!-- WRONG: Template tag split across lines -->
{% if user.is_authenticated %}
    <p>Welcome, {{ user.username }}!</p>
{% endif
%}

<!-- WRONG: Incomplete template tag -->
{% if user.is_authenticated
    <p>Welcome, {{ user.username }}!</p>
{% endif %}
```

### 2. Template Tag Nesting

#### ✅ Correct Nesting

```django
{% if user.is_authenticated %}
    {% for item in cart_items %}
        <div class="cart-item">
            {{ item.name }}
        </div>
    {% endfor %}
{% endif %}
```

#### ❌ Incorrect Nesting

```django
<!-- WRONG: Unclosed tags -->
{% if user.is_authenticated %}
    {% for item in cart_items %}
        <div class="cart-item">
            {{ item.name }}
        </div>
    {% endfor %}
<!-- Missing {% endif %} -->
```

### 3. Template Variable Usage

#### ✅ Correct Variable Usage

```django
{{ user.get_full_name|default:user.username }}
{{ product.price|floatformat:2 }}
{{ request.user.is_authenticated }}
```

#### ❌ Incorrect Variable Usage

```django
<!-- WRONG: Unescaped user input -->
{{ user_input|safe }}

<!-- WRONG: Missing filters for user data -->
{{ user.bio }}
```

## Common Issues and Solutions

### Issue 1: Unclosed Template Tags

**Problem:**

```
TemplateSyntaxError: Unclosed tag on line X: 'if'. Looking for one of: endif.
```

**Solution:**

- Always ensure every opening tag has a corresponding closing tag
- Use proper indentation to track tag pairs
- Use template validation tools

**Example Fix:**

```django
<!-- Before (BROKEN) -->
{% if LANGUAGE_CODE == 'fa' %}تغییر تم{% else %}Toggle Theme{%
endif %}

<!-- After (FIXED) -->
{% if LANGUAGE_CODE == 'fa' %}تغییر تم{% else %}Toggle Theme{% endif %}
```

### Issue 2: Template Tags Split Across Lines

**Problem:**
Template tags that are incorrectly split across multiple lines cause syntax errors.

**Solution:**

- Keep template tags on single lines when possible
- If splitting is necessary, ensure proper continuation

**Example Fix:**

```django
<!-- Before (BROKEN) -->
<span class="ms-2"
  >{% if LANGUAGE_CODE == 'fa' %}تغییر تم{% else %}Toggle Theme{%
  endif %}</span
>

<!-- After (FIXED) -->
<span class="ms-2">{% if LANGUAGE_CODE == 'fa' %}تغییر تم{% else %}Toggle Theme{% endif %}</span>
```

### Issue 3: Missing Template Load Tags

**Problem:**
Using template tags without loading them first.

**Solution:**
Always load required template tags at the top of the template.

```django
{% load static %}
{% load i18n %}
{% load humanize %}
```

## Best Practices

### 1. Template Organization

#### File Structure

```
templates/
├── base.html                 # Base template
├── components/              # Reusable components
│   ├── navbar.html
│   ├── footer.html
│   └── forms/
├── includes/                # Template includes
│   ├── head.html
│   └── scripts.html
└── [app_name]/             # App-specific templates
    ├── [model_name]_list.html
    ├── [model_name]_detail.html
    └── [model_name]_form.html
```

#### Template Inheritance

```django
<!-- base.html -->
<!DOCTYPE html>
<html lang="{% get_current_language as LANGUAGE_CODE %}{{ LANGUAGE_CODE }}">
<head>
    {% include 'includes/head.html' %}
    {% block extra_css %}{% endblock %}
</head>
<body>
    {% include 'components/navbar.html' %}

    <main class="container">
        {% block content %}{% endblock %}
    </main>

    {% include 'components/footer.html' %}
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 2. Template Tag Best Practices

#### Use Semantic Template Tags

```django
<!-- Good: Clear and semantic -->
{% if user.is_authenticated %}
    {% include 'components/user_menu.html' %}
{% else %}
    {% include 'components/auth_links.html' %}
{% endif %}

<!-- Avoid: Complex logic in templates -->
{% if user.is_authenticated and user.has_permission and not user.is_suspended %}
    <!-- Complex logic should be in views -->
{% endif %}
```

#### Proper Filter Usage

```django
<!-- Good: Appropriate filters -->
{{ product.price|floatformat:2 }}
{{ user.bio|truncatewords:30 }}
{{ post.created_at|timesince }}

<!-- Good: Safe handling of user input -->
{{ user_input|escape }}
{{ user_input|striptags }}
```

### 3. Static File Management

#### Proper Static File Usage

```django
{% load static %}

<!-- Good: Using static template tag -->
<link rel="stylesheet" href="{% static 'css/main.css' %}">
<img src="{% static 'img/logo.png' %}" alt="Logo">

<!-- Avoid: Hardcoded paths -->
<link rel="stylesheet" href="/static/css/main.css">
<img src="/static/img/logo.png" alt="Logo">
```

### 4. URL Management

#### Proper URL Usage

```django
<!-- Good: Using url template tag -->
<a href="{% url 'products:product_detail' product.id %}">View Product</a>
<a href="{% url 'users:profile' %}">Profile</a>

<!-- Avoid: Hardcoded URLs -->
<a href="/products/{{ product.id }}/">View Product</a>
<a href="/users/profile/">Profile</a>
```

## Template Structure

### 1. Template Blocks

#### Required Blocks

Every template should include these standard blocks:

```django
{% extends 'base.html' %}

{% block title %}Page Title{% endblock %}

{% block extra_css %}
    <!-- Page-specific CSS -->
{% endblock %}

{% block content %}
    <!-- Main content -->
{% endblock %}

{% block extra_js %}
    <!-- Page-specific JavaScript -->
{% endblock %}
```

### 2. Template Includes

#### Component Includes

```django
<!-- Reusable components -->
{% include 'components/navbar.html' %}
{% include 'components/footer.html' %}
{% include 'components/product_card.html' with product=item %}
```

#### Conditional Includes

```django
{% if user.is_authenticated %}
    {% include 'components/user_dashboard.html' %}
{% else %}
    {% include 'components/welcome_message.html' %}
{% endif %}
```

## Performance Considerations

### 1. Database Query Optimization

#### Avoid N+1 Queries

```django
<!-- Bad: N+1 queries -->
{% for product in products %}
    <div>{{ product.category.name }}</div>  <!-- Database query for each product -->
{% endfor %}

<!-- Good: Use select_related in view -->
# In view:
products = Product.objects.select_related('category').all()

# In template:
{% for product in products %}
    <div>{{ product.category.name }}</div>  <!-- No additional queries -->
{% endfor %}
```

#### Use Template Caching

```django
{% load cache %}

{% cache 500 sidebar %}
    {% include 'components/sidebar.html' %}
{% endcache %}
```

### 2. Template Optimization

#### Minimize Template Logic

```django
<!-- Bad: Complex logic in template -->
{% if user.is_authenticated and user.has_permission and user.is_active and not user.is_suspended %}
    <!-- Complex condition -->
{% endif %}

<!-- Good: Move logic to view or template tag -->
{% if user.can_access_feature %}
    <!-- Simple condition -->
{% endif %}
```

## Security Guidelines

### 1. Input Sanitization

#### Always Escape User Input

```django
<!-- Good: Escaped user input -->
{{ user_input|escape }}
{{ user_input|striptags }}

<!-- Bad: Unsafe user input -->
{{ user_input|safe }}  <!-- Only use if you're absolutely sure it's safe -->
```

#### Use Safe Filters Carefully

```django
<!-- Good: Safe for trusted content -->
{{ trusted_html_content|safe }}

<!-- Bad: Unsafe for user input -->
{{ user_input|safe }}  <!-- Potential XSS vulnerability -->
```

### 2. CSRF Protection

#### Always Include CSRF Token

```django
<form method="post">
    {% csrf_token %}
    <!-- Form fields -->
</form>
```

## Accessibility Guidelines

### 1. Semantic HTML

#### Use Proper HTML Elements

```django
<!-- Good: Semantic elements -->
<nav role="navigation" aria-label="Main navigation">
    <ul>
        <li><a href="{% url 'home' %}">Home</a></li>
    </ul>
</nav>

<!-- Bad: Non-semantic elements -->
<div class="nav">
    <div class="nav-item">
        <span onclick="goToHome()">Home</span>
    </div>
</div>
```

### 2. ARIA Labels and Roles

#### Proper ARIA Usage

```django
<!-- Good: Proper ARIA attributes -->
<button type="button" aria-label="Close dialog" aria-expanded="false">
    <span aria-hidden="true">&times;</span>
</button>

<img src="{% static 'img/chart.png' %}" alt="Sales chart showing 25% increase" />
```

## Validation Tools

### 1. Django Management Command

Use the custom template validation command:

```bash
# Validate all templates
python manage.py validate_templates

# Validate specific template
python manage.py validate_templates --template templates/components/navbar.html

# Verbose output
python manage.py validate_templates --verbose
```

### 2. Template Linter Script

Use the advanced template linter:

```bash
# Lint all templates
python scripts/template_linter.py

# Lint specific file
python scripts/template_linter.py --file templates/components/navbar.html

# Verbose output with suggestions
python scripts/template_linter.py --verbose

# JSON output
python scripts/template_linter.py --format json
```

### 3. IDE Integration

#### VS Code Extensions

- Django Template Support
- HTML CSS Support
- Prettier (for HTML formatting)

#### PyCharm

- Django Template Language support
- Template syntax highlighting
- Template tag completion

## Common Template Patterns

### 1. Conditional Content

```django
{% if user.is_authenticated %}
    <p>Welcome back, {{ user.username }}!</p>
    <a href="{% url 'users:logout' %}">Logout</a>
{% else %}
    <p>Please <a href="{% url 'users:login' %}">login</a> to continue.</p>
{% endif %}
```

### 2. Loop with Empty State

```django
{% if products %}
    {% for product in products %}
        <div class="product-card">
            <h3>{{ product.name }}</h3>
            <p>{{ product.description|truncatewords:20 }}</p>
        </div>
    {% endfor %}
{% else %}
    <div class="empty-state">
        <p>No products found.</p>
    </div>
{% endif %}
```

### 3. Pagination

```django
{% if is_paginated %}
    <nav aria-label="Pagination">
        <ul class="pagination">
            {% if page_obj.has_previous %}
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}">Previous</a>
                </li>
            {% endif %}

            <li class="page-item active">
                <span class="page-link">{{ page_obj.number }} of {{ page_obj.paginator.num_pages }}</span>
            </li>

            {% if page_obj.has_next %}
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.next_page_number }}">Next</a>
                </li>
            {% endif %}
        </ul>
    </nav>
{% endif %}
```

## Troubleshooting

### Common Error Messages

1. **"Unclosed tag"**: Check for missing closing tags
2. **"Invalid block tag"**: Verify template tag syntax
3. **"Template does not exist"**: Check template path and TEMPLATES setting
4. **"Variable does not exist"**: Ensure variable is passed in context

### Debugging Tips

1. Use `{% debug %}` template tag to inspect context
2. Check Django template documentation
3. Use template validation tools
4. Test templates in isolation
5. Check for typos in template tag names

## Conclusion

Following these guidelines will help you create maintainable, secure, and performant Django templates. Always validate your templates using the provided tools and follow the established patterns for consistency across your project.
