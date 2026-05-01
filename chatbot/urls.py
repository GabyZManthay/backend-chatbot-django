from rest_framework.routers import DefaultRouter
from .views import DocumentoViewSet
from .views import (
    UsuarioViewSet,
)

from .views import (
    PerguntaViewSet,
    ConversaViewSet,
)

router = DefaultRouter()

router.register('documentos', DocumentoViewSet)
router.register('usuarios', UsuarioViewSet)


# NOVOS endpoints
router.register('perguntas', PerguntaViewSet)
router.register('conversas', ConversaViewSet)



urlpatterns = router.urls

# from rest_framework.routers import DefaultRouter
# # ✅ Juntei todos os imports para ficar mais organizado
# from .views import (
#     DocumentoViewSet,
#     UsuarioViewSet,
#     PerguntaViewSet,
#     ConversaViewSet,
# )

# router = DefaultRouter()

# router.register('documentos', DocumentoViewSet)
# router.register('usuarios', UsuarioViewSet)

# # NOVOS endpoints
# router.register('perguntas', PerguntaViewSet)
# router.register('conversas', ConversaViewSet)

# # ✅ Atribui as URLs geradas pelo router
# urlpatterns = router.urls