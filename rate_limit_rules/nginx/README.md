# Nginx Rate Limit Configuration

This directory contains the automatically generated Nginx rate limit configuration file.

## Generated File

*   **`nginx_rate_limit.conf`**: The main Nginx rate limit configuration file generated from `config.yaml`.

## Integration

To integrate this configuration with your Nginx server:

1.  **Copy the configuration file to your server:**
    ```bash
    scp nginx_rate_limit.conf user@your-server:/path/to/nginx/conf.d/
    ```

2.  **Include it in your Nginx configuration:**
    Edit your `nginx.conf` file and add:
    ```nginx
    http {
        include /path/to/nginx/conf.d/nginx_rate_limit.conf;
        # ... other configurations
    }
    ```

3.  **Test the configuration:**
    ```bash
    nginx -t
    ```

4.  **Reload Nginx:**
    ```bash
    nginx -s reload
    # or
    systemctl reload nginx
    ```

## Configuration Structure

The generated file includes:

*   **Rate limit zones**: Defines memory zones for tracking request rates
*   **Location blocks**: Applies rate limits to specific paths
*   **Global limits**: Default rate limiting for all locations

## Troubleshooting

*   **Error: "limit_req_zone" directive is duplicate**: Ensure you don't have conflicting rate limit zones defined elsewhere in your Nginx configuration.
*   **Rate limits not working**: Verify that the `limit_req` directive is placed correctly within your location blocks.

## Resources

*   [Nginx Rate Limiting Documentation](https://docs.nginx.com/nginx/admin-guide/security/rate-limiting/)
*   [Nginx limit_req Module](http://nginx.org/en/docs/http/ngx_http_limit_req_module.html)
