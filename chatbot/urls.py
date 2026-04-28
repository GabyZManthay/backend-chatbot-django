from rest_framework.routers import DefaultRouter
from .views import DocumentoViewSet
from .views import (
    UsuarioViewSet,
)

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PerguntaViewSet,
    ConversaViewSet,
    PerguntarAPIView
)

router = DefaultRouter()

router.register('documentos', DocumentoViewSet)
router.register('usuarios', UsuarioViewSet)


# NOVOS endpoints
router.register('perguntas', PerguntaViewSet)
router.register('conversas', ConversaViewSet)



urlpatterns = router.urls

urlpatterns = [
    # ✅ Rotas do router (CRUDs automáticos)
    path('', include(router.urls)),
    
    # ✅ Endpoint do chatbot (NLP)
    path('perguntar/', PerguntarAPIView.as_view(), name='perguntar'),
]

