import pytest
from decimal import Decimal

from orders.models import Order

pytestmark = [pytest.mark.django_db]


def get_order():
    return Order.objects.last()


def test_order(call_purchase, course):
    call_purchase()

    placed = get_order()

    assert placed.item == course
    assert placed.price == Decimal('1900.00')
    assert not hasattr(placed, 'study')  # Study record is not created yet, because order is not paid


def test_user(call_purchase, course):
    call_purchase()

    placed = get_order()

    assert placed.user.first_name == 'Забой'
    assert placed.user.last_name == 'Шахтёров'
    assert placed.user.email == 'zaboy@gmail.com'


@pytest.mark.parametrize('wants_to_subscribe', [True, False])
def test_user_auto_subscription(call_purchase, wants_to_subscribe):
    call_purchase(subscribe=wants_to_subscribe)

    placed = get_order()

    assert placed.user.subscribed is wants_to_subscribe


def test_subscription_tags(call_purchase, subscribe):
    call_purchase(subscribe=True)

    placed = get_order()

    subscribe.assert_called_once_with(user=placed.user, tags=['ruloning-oboev'])


def test_by_default_user_is_not_subscribed(call_purchase):
    call_purchase()

    placed = get_order()

    assert placed.user.subscribed is False


def test_redirect(api, course, default_user_data):
    response = api.post('/api/v2/courses/ruloning-oboev/purchase/', {
        **default_user_data,
    }, format='multipart', expected_status_code=302, as_response=True)

    assert response.status_code == 302
    assert response['Location'] == 'https://bank.test/pay/'


def test_custom_success_url(call_purchase, bank):
    call_purchase(success_url='https://ok.true/yes')
    assert bank.call_args[1]['success_url'] == 'https://ok.true/yes'


def test_invalid(client):
    response = client.post('/api/v2/courses/ruloning-oboev/purchase/', {})

    assert response.status_code == 400
