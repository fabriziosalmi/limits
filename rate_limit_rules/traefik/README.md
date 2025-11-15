# Traefik Rate Limit Configuration

This directory contains the automatically generated Traefik rate limit configuration file.

## Generated File

*   **`traefik_rate_limit.conf`**: The main Traefik rate limit configuration file generated from `config.yaml`.

## Integration

To integrate this configuration with your Traefik server:

1.  **Copy the content to your Traefik configuration file:**
    The generated file contains middleware definitions that need to be merged into your `traefik.yml` or `traefik.toml` file.

2.  **For YAML configuration (`traefik.yml`):**
    ```yaml
    http:
      middlewares:
        # Paste the generated middleware configurations here
        
      routers:
        my-router:
          rule: "Host(`example.com`)"
          middlewares:
            - rate-limit-global  # Add your rate limit middleware
          service: my-service
    ```

3.  **For TOML configuration (`traefik.toml`):**
    ```toml
    [http.middlewares]
      # Paste the generated middleware configurations here
      
    [http.routers.my-router]
      rule = "Host(`example.com`)"
      middlewares = ["rate-limit-global"]
      service = "my-service"
    ```

4.  **Restart Traefik:**
    ```bash
    systemctl restart traefik
    # or if running in Docker
    docker restart traefik
    ```

## Configuration Structure

The generated file includes:

*   **Middleware definitions**: Rate limiting middlewares for different paths
*   **Global rate limits**: Default rate limiting middleware
*   **Path-specific middlewares**: Custom rate limits for specific routes

## Troubleshooting

*   **Middleware not applying**: Ensure the middleware name matches exactly in your router configuration.
*   **Rate limits not working**: Check Traefik logs for any configuration errors.
*   **Syntax errors**: Validate your YAML/TOML syntax using online validators.

## Resources

*   [Traefik Rate Limiting Documentation](https://doc.traefik.io/traefik/middlewares/http/ratelimit/)
*   [Traefik Middleware Configuration](https://doc.traefik.io/traefik/middlewares/overview/)
