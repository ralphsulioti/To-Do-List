from django.test import TestCase, Client
from django.urls import reverse
from .models import List, Item
from django.contrib.auth.models import User
from django.utils import timezone

# Tests user creation, login, and logout
class UserAuthenticationTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_login_logout(self):
        # Simulate user login
        self.client.force_login(self.user)
        self.assertTrue(self.user.is_authenticated)

        # Test user logout
        logout_url = reverse('logout_view')  # Assuming you have a URL named 'logout' for the logout functionality
        response = self.client.get(logout_url)

        # Check if the user is logged out
        self.assertFalse(response.wsgi_request.user.is_authenticated)

# Tests if adding and removing a list works
class AddListTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_add_list(self):
        # Login the test user
        self.client.login(username='testuser', password='12345')

        # Count the initial number of lists
        initial_count = List.objects.count()

        # Post request to add a new list
        response = self.client.post(reverse('add_list'), {'list_name': 'Test List'})

        # Check if the request was successful and redirected to the correct URL
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('lists_index'))

        # Check if the list was added to the database
        self.assertEqual(List.objects.count(), initial_count + 1)
        new_list = List.objects.last()
        self.assertEqual(new_list.list_name, 'Test List')
        self.assertEqual(new_list.user_id, self.user)

        # Test removal of list
        List.objects.filter(list_name='Test List').delete()

        # Check if list was removed from the database
        self.assertEqual(List.objects.count(), initial_count)

        # Log the user out
        self.client.logout()

# Testing if adding and removing an item works
class AddItemTest(TestCase):
    def setUp(self):
        # Create objects for test
        self.user = User.objects.create_user(username='testuser', password='12345')

        self.list = List.objects.create(user_id=self.user, list_name='Test List')

    def test_add_item(self):
        # Count the initial number of items
        initial_count = Item.objects.count()

        # Log in the user (if needed)
        self.client.login(username='testuser', password='12345')

        # Simulate adding an item
        response = self.client.post('/add/{}/'.format(self.list.id), {'item_descr': 'Test Item'})

        # Check if the item was added successfully (redirects to list view)
        self.assertEqual(response.status_code, 302)

        # Check if the number of items increased by 1
        self.assertEqual(Item.objects.count(), initial_count + 1)

        # Get the added item
        added_item = Item.objects.latest('item_date_added')

        # Check if the added item belongs to the correct list
        self.assertEqual(added_item.list_id, self.list)

        # Check if the item description is correct
        self.assertEqual(added_item.item_descr, 'Test Item')

        # Check if the item is not done by default
        self.assertFalse(added_item.item_done)

        # Remove the item
        Item.objects.filter(item_descr='Test Item').delete()

        # Check if the item is removed correctly
        self.assertEqual(Item.objects.count(), initial_count)

        # Log the user out
        self.client.logout()


class ItemDoneTest(TestCase):
    def setUp(self):
        # Create objects for test
        self.user = User.objects.create_user(username='testuser', password='12345')

        self.list = List.objects.create(user_id=self.user, list_name='Test List')

        self.item = Item.objects.create(list_id=self.list, item_date_added=timezone.now(), item_descr='Test Item', item_done=False)

        self.client = Client()

    def test_item_done(self):
        # Log in the user (if needed)
        self.client.login(username='testuser', password='12345')

        # Mark the item as done
        response = self.client.post(reverse('item_done', kwargs={'item_id':self.item.id}))

        # Check if the response status code is 302 (redirect)
        self.assertEqual(response.status_code, 302)

        # Refresh the item from the database
        self.item.refresh_from_db()

        # Check if the item is now marked as done
        self.assertTrue(self.item.item_done)

        # Log the user out
        self.client.logout()


class ListViewTestCase(TestCase):
    def setUp(self):
        # Create objects for test
        self.user = User.objects.create_user(username='testuser', password='12345')

        self.list = List.objects.create(user_id=self.user, list_name='Test List')

        self.item1 = Item.objects.create(list_id=self.list, item_descr='Item 1', item_done=False, item_date_added=timezone.now())
        self.item2 = Item.objects.create(list_id=self.list, item_descr='Item 2', item_done=True, item_date_added=timezone.now())

        self.client = Client()

    def test_list_view(self):
        # Log in the user
        self.client.login(username='testuser', password='12345')

        # Make a GET request to the list view
        response = self.client.get(reverse('list_view', kwargs={'list_id': self.list.id}))

        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Check if the correct list is being passed to the template
        self.assertEqual(response.context['list_obj'], self.list)

        # Check if the correct items are being passed to the template and are sorted by default
        expected_items = [self.item1, self.item2]
        actual_items = list(response.context['list_items'])
        self.assertEqual(expected_items, actual_items)

        # Logging the user out
        self.client.logout()

class ItemDetailsTest(TestCase):
    def setUp(self):
        # Create objects for test
        self.user = User.objects.create_user(username='testuser', password='12345')

        self.list = List.objects.create(user_id=self.user, list_name='Test List')

        self.item = Item.objects.create(list_id=self.list, item_date_added=timezone.now(), item_descr='Test Item', item_done=False)

        self.client = Client()

    def test_item_details(self):
        # Logging the user in
        self.client.login(username='testuser', password='12345')

        # Grabbing the item details
        response = self.client.post(reverse('item_details', kwargs={'item_id':self.item.id}))

        # Check if the status code is 200
        self.assertEqual(response.status_code, 200)

        # Check if the right details are given based on the response's context
        self.assertEqual(response.context['item'], self.item)
        self.assertEqual(response.context['list_name'], self.list.list_name)

        # Logging the user out
        self.client.logout()
