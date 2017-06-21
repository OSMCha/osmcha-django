from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.schemas import SchemaGenerator
from rest_framework.views import APIView
from rest_framework_swagger import renderers


class SwaggerSchemaView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [
        renderers.OpenAPIRenderer,
        renderers.SwaggerUIRenderer
        ]

    @classmethod
    def as_view(self, url_pattern=None, **kwargs):
        view = super(SwaggerSchemaView, self).as_view(**kwargs)
        self.url_pattern = url_pattern
        return view

    def get(self, request):
        generator = SchemaGenerator(
            patterns=self.url_pattern,
            title='OSMCHA API'
            )
        schema = generator.get_schema()

        return Response(schema)
