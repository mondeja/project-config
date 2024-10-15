########
Fetching
########

The online resource request process performed by project-config
can be configured in detail using environment variables.

All requests are affected by the next environment variables:

* ``PROJECT_CONFIG_REQUESTS_TIMEOUT``: The maximum time in seconds
  to wait for a resource to be fetched. Default is 10 seconds.

******
GitHub
******

The next URL patterns are considered GitHub sources and are fetched
through the GitHub API:

* ``gh://<user>/<repo>[@<tag>]``: Fetches the content of a GitHub
  repository. The tag is optional and can be a branch, tag or commit
  hash. If not provided, the default branch is used.
* ``https://github.com/<user>/<repo>/...``: Fetches the content of a
  GitHub repository. The URL can point to any file or directory.

Note that ``https://raw.githubusercontent.com/...`` URLs are
considered normal HTTP requests.

The next environment variables can be used to configure GitHub requests:

* ``GITHUB_TOKEN``: A GitHub token to authenticate requests. This is
  useful to avoid rate limiting and to access private repositories.
