# Logging

Managed logging can write to a rotating UTF-8 file, the console, or both. It uses an application-specific logger and does not replace host handlers. Tokens, authorization headers, and sensitive URL components are filtered from package messages.

Disable managed logging when the host already owns all formatting and routing. Task log storage remains the application's responsibility; `/log` only dispatches to the configured handler.
