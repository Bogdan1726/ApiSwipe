from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser, JSONParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from drf_psq import PsqMixin, Rule
from rest_framework.viewsets import GenericViewSet
from .permissions import IsMyFilter
from .services.month_ahead import get_range_month
from .models import (
    Notary, Contact, Subscription, Message, Filter
)
from .serializers import (
    NotarySerializer, UserProfileSerializer, UserAgentSerializer,
    UserSubscriptionSerializer, MessageSerializer, FilterSerializer,
    UserNotificationSerializer, UserPerAgentSerializer,
    UserAutoRenewalSubscriptionSerializer, UserListSerializer
)

User = get_user_model()


# Create your views here.

@extend_schema(
    description='Management a user filters. Permissions: [IsMyFilter, IsAuthenticated]'
)
class FilterViewSet(PsqMixin,
                    mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.ListModelMixin,
                    GenericViewSet
                    ):
    serializer_class = FilterSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]
    http_method_names = ['get', 'post', 'put']

    psq_rules = {
        ('update', 'retrieve'): [Rule([IsMyFilter])]
    }

    def get_queryset(self):
        queryset = Filter.objects.filter(user=self.request.user).select_related('user')
        return queryset


@extend_schema(methods=['GET'], description='Get list notaries. Permissions: IsAuthenticated')
@extend_schema(
    methods=['PUT', 'POST', 'DELETE'],
    description='Management a notaries(delete, update and create new) Permissions: IsAdminUser'
)
class NotaryViewSet(PsqMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = NotarySerializer
    queryset = Notary.objects.all()
    parser_classes = [MultiPartParser]
    http_method_names = ['get', 'post', 'put', 'delete']

    psq_rules = {
        ('list', 'retrieve'): [Rule([IsAuthenticated])]
    }

    @extend_schema(responses=status.HTTP_200_OK,
                   description='Delete notary Permissions: IsAdminUser',
                   examples=[OpenApiExample('Example',
                                            value={'message': 'Delete notary success', 'status': status.HTTP_200_OK})])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            data={
                'message': 'Delete notary success',
                'status': status.HTTP_200_OK
            },
            status=status.HTTP_200_OK
        )


@extend_schema(
    methods=['GET'],
    parameters=[
        OpenApiParameter(
            name='user_id',
            description='Optional query parameter to get the message history of a specific user',
            required=False, type=int
        )
    ]
)
@extend_schema(
    description='Messaging between users and between the user and technical support. Permissions: IsAuthenticated')
class MessageViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     GenericViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        queryset = Message.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user),
        ).prefetch_related('message_files')
        if user_id is not None:
            queryset = Message.objects.filter(
                Q(sender=self.request.user, recipient_id=user_id)
                |
                Q(sender_id=user_id, recipient=self.request.user)
            ).prefetch_related('message_files')
        return queryset


class UserProfileViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(description='Get user data, Permissions: IsAuthenticated', methods=["GET"])
    @action(detail=False)
    def get_profile(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(description='Update user data, Permissions: IsAuthenticated', methods=["PUT"])
    @action(detail=False, methods=['PUT'])
    def update_profile(self, request):
        serializer = self.serializer_class(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(description='Update user notification, Permissions: IsAuthenticated', methods=["PUT"])
    @action(detail=False, methods=['PUT'], serializer_class=UserNotificationSerializer)
    def update_notification(self, request):
        serializer = self.serializer_class(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(description='Switch calls and messages per agent, Permissions: IsAuthenticated', methods=["PUT"])
    @action(detail=False, methods=['PUT'], serializer_class=UserPerAgentSerializer)
    def switch_to_agent(self, request):
        serializer = self.serializer_class(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserAgentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserAgentSerializer
    parser_classes = [MultiPartParser]

    @extend_schema(description='Get agent data, Permissions: IsAuthenticated', methods=["GET"])
    @action(detail=False)
    def get_agent(self, request):
        obj = get_object_or_404(Contact, user=request.user)
        serializer = self.serializer_class(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(description='Update agent data, Permissions: IsAuthenticated', methods=["PUT"])
    @action(detail=False, methods=['PUT'])
    def update_agent(self, request):
        obj = get_object_or_404(Contact, user=request.user)
        serializer = self.serializer_class(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserSubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSubscriptionSerializer

    @extend_schema(description='Get subscription, Permissions: IsAuthenticated', methods=['GET'])
    @action(detail=False)
    def get_subscription(self, request):
        obj = get_object_or_404(Subscription, user=request.user)
        serializer = self.serializer_class(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(description='Activate not active subscription, Permissions: IsAuthenticated', methods=['PUT'])
    @action(detail=False, methods=['PUT'])
    def active_subscription(self, request):
        obj = get_object_or_404(
            Subscription,
            user=request.user,
            is_active=False
        )
        obj.date_end = get_range_month().date()
        obj.is_active = True
        obj.is_auto_renewal = True
        serializer = self.serializer_class(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(description='Renew your subscription, Permissions: IsAuthenticated', methods=['PUT'])
    @action(detail=False, methods=['PUT'])
    def update_subscription(self, request):
        obj = get_object_or_404(
            Subscription,
            user=request.user,
            is_active=True
        )
        obj.date_end = get_range_month(obj.date_end)
        serializer = self.serializer_class(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(description='Enable or disable auto-renewal of a subscription, Permissions: IsAuthenticated',
                   methods=['PUT'])
    @action(
        detail=False,
        methods=['PUT'],
        serializer_class=UserAutoRenewalSubscriptionSerializer,
        parser_classes=[JSONParser]

    )
    def auto_renewal_subscription(self, request):
        obj = get_object_or_404(Subscription, user=request.user)
        serializer = self.serializer_class(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(description='List all users and filter for user in blacklist. Permissions: IsAdminUser')
class UserListViewSet(PsqMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.ListModelMixin,
                      GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_blacklist']
    search_fields = ['id', 'first_name', 'last_name', 'phone', 'email']
    http_method_names = ['get', 'post', 'put']

    def get_queryset(self):
        queryset = User.objects.filter(is_staff=False, is_developer=False)
        return queryset


@api_view(['GET'])
@permission_classes((AllowAny,))
def success_email_verify(request):
    return Response('Подтверждения электронной почты выполнено успешно')
