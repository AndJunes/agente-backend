"""The HTTP boundary: routes, request validation, SSE streaming and the chat use case.

Public routes (the complete list - anything else is a 404):

    GET  /                                  the web page
    GET  /api/v1/health                     liveness and configuration summary
    GET  /api/v1/locales                    supported locales and the default one
    GET  /api/v1/i18n/{locale}              UI strings of a locale
    GET  /api/v1/demos?locale=xx            the prepared demos, localised
    GET  /api/v1/artifacts/{id}/download    the verified ZIP of a generated project
    GET  /api/v1/blockchain/agent           the optional Stellar identity panel
    POST /api/v1/chat                       ask a question; answers with Server-Sent Events
"""
