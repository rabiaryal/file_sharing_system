from django.apps import AppConfig
from django.db.models.signals import post_migrate


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        from django.contrib.auth.management import create_permissions

        post_migrate.disconnect(
            create_permissions,
            dispatch_uid="django.contrib.auth.management.create_permissions",
        )
        post_migrate.connect(
            self.safe_create_permissions,
            dispatch_uid="users.safe_create_permissions",
        )

    @staticmethod
    def safe_create_permissions(sender, app_config, using, **kwargs):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        if app_config.models_module is None:
            return

        for model in app_config.get_models():
            content_type = ContentType.objects.db_manager(using).get_for_model(
                model,
                for_concrete_model=False,
            )

            permissions = list(model._meta.permissions)
            if model._meta.default_permissions:
                for action in model._meta.default_permissions:
                    permissions.append(
                        (
                            f"{action}_{model._meta.model_name}",
                            f"Can {action} {model._meta.verbose_name_raw}",
                        )
                    )

            for codename, name in permissions:
                Permission.objects.using(using).get_or_create(
                    content_type=content_type,
                    codename=codename,
                    defaults={"name": str(name)},
                )