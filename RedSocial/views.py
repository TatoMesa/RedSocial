from django.shortcuts import render
from django.views.generic import TemplateView, DetailView, UpdateView, ListView
from django.views.generic.edit import CreateView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


from .forms import RegistrationForm, LoginForm
from profiles.forms import FollowForm
from profiles.models import UserProfile, Follow
from posts.models import Post


class HomeView(TemplateView):
    template_name = "general/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        last_posts = Post.objects.all().order_by('-created_at')[:15]
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, 'profile'):
                seguidos = Follow.objects.filter(
                    follower=self.request.user.profile
                ).values_list('following__user', flat=True)
                last_posts = Post.objects.filter(
                    user__in=seguidos
                ).order_by('-created_at')[:15]
        context['last_posts'] = last_posts
        return context


class LoginView(FormView):
    template_name = "general/login.html"
    form_class = LoginForm
    def form_valid(self, form):
        usuario = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username= usuario, password=password)

        if user is not None:
            login(self.request, user)
            messages.add_message(self.request, messages.SUCCESS, f'Bienvenido {user.username}')
            return HttpResponseRedirect(reverse_lazy('home'))
        else:
            messages.add_message(self.request, messages.ERROR, ('Usuario o Contraseña incorrecta'))
            return super(LoginView, self).form_invalid(form)


class RegisterView(CreateView):
    template_name = "general/register.html"
    model = User
    success_url = reverse_lazy('login')
    form_class = RegistrationForm

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, 'Usuario registrado con exito.')
        return super(RegisterView, self).form_valid(form)


class LegalView(TemplateView):
    template_name = "general/legal.html"


class ContactView(TemplateView):
    template_name = "general/contact.html"
@method_decorator(login_required, name='dispatch')
class ProfileDetailView(DetailView, FormView):
    model = UserProfile
    template_name = "general/profile_detail.html"
    context_object_name = "profile"
    form_class = FollowForm

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_initial(self):
        return {
            'profile_pk': self.get_object().pk
        }

    def form_valid(self, form):
        profile_pk = form.cleaned_data.get('profile_pk')
        following = UserProfile.objects.get(pk=profile_pk)

        existing = Follow.objects.filter(
            follower=self.request.user.profile,
            following=following
        )

        if existing.exists():
            existing.delete()
            messages.success(
                self.request,
                f"Has dejado de seguir a {following.user.username}"
            )
        else:
            Follow.objects.create(
                follower=self.request.user.profile,
                following=following
            )
            messages.success(
                self.request,
                f"Ahora sigues a {following.user.username}"
            )

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'profile_detail',
            args=[self.get_object().pk]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        following = Follow.objects.filter(
            follower=self.request.user.profile,
            following=self.get_object()
        ).exists()

        context['following'] = following
        return context


class ProfileListView(ListView):
    model = UserProfile
    template_name = "general/profile_list.html"
    context_object_name = "profiles"

    def get_queryset(self):
        # Empezamos con todos los perfiles
        queryset = UserProfile.objects.all().order_by('user__username')
        # 1. Excluimos SIEMPRE a los superusuarios (el admin)
        queryset = queryset.exclude(user__is_superuser=True)
        # 2. Si el usuario está logueado, lo excluimos a él también para que no se vea a sí mismo
        if self.request.user.is_authenticated:
            queryset = queryset.exclude(user=self.request.user)
        return queryset

@method_decorator(login_required, name='dispatch')
class ProfileUpdateView(UpdateView):
    model = UserProfile
    template_name = "general/profile_update.html"
    context_object_name = "profile"
    fields = ['profile_picture', 'bio', 'birth_date']

    def dispatch(self, request, *args, **kwargs):
        user_profile = self.get_object()
        if user_profile.user != self.request.user:
            return HttpResponseRedirect(reverse_lazy('home'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, 'Perfil editado con exito.')
        return super(ProfileUpdateView, self).form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('profile_detail', args=[self.object.pk])

    
@login_required
def logout_view(request):
    logout(request)
    messages.add_message(request, messages.INFO, 'Sesión cerrada con exito.')
    return HttpResponseRedirect(reverse_lazy('home'))