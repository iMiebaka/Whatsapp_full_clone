from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    re_password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    class Meta:
        model = User
        fields = ["first_name", "username", "email", 'password', 're_password']
        extra_kwargs = {
            'password': {'write_only': True }
        }
    def save(self):
        user_accounts = User.objects.create_user(
            username=self.validate_data['username'],
            email_address=self.validate_data['email'],
        )
        password = self.validate_data['password']
        re_password = self.validate_data['re_password']
        if password != re_password:
            raise serializers.ValidationError({'error': 'Password does not match'})
        user_accounts.set_password(password)
        user_accounts.self.validate_data['first_name']
        user_accounts.save()

    def validate(self, data):
        if data['password'] != data['re_password']:
            raise serializers.ValidationError({'error': 'Password does not match'})
        if User.objects.filter(username__iexact=data['username']).exists():
            raise serializers.ValidationError({'error': 'Username already exist'})
        if User.objects.filter(email__iexact=data['email']).exists():
            raise serializers.ValidationError({'error': 'Username already exist'})
        print('Validation Check')
        return data
