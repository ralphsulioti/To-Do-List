from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Item, List

GOOGLE_PROVIDER_WITHOUT_APP = {"google": {"SCOPE": ["profile", "email"]}}
GOOGLE_PROVIDER_WITH_APP = {
    "google": {
        "SCOPE": ["profile", "email"],
        "APPS": [{"client_id": "test-client-id", "secret": "test-secret", "key": ""}],
    }
}


# Tests the home page with and without Google sign-in configured
class HomePageTest(TestCase):
    @override_settings(
        GOOGLE_LOGIN_ENABLED=False, SOCIALACCOUNT_PROVIDERS=GOOGLE_PROVIDER_WITHOUT_APP
    )
    def test_home_without_google(self):
        response = self.client.get(reverse("home"))

        # The page renders with local login and signup, and no Google button
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("account_login"))
        self.assertContains(response, reverse("account_signup"))
        self.assertNotContains(response, "Sign in with Google")

    @override_settings(
        GOOGLE_LOGIN_ENABLED=True, SOCIALACCOUNT_PROVIDERS=GOOGLE_PROVIDER_WITH_APP
    )
    def test_home_with_google(self):
        response = self.client.get(reverse("home"))

        # The Google button is a POST form to allauth's Google login URL
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in with Google")
        self.assertContains(
            response, f'method="post" action="{reverse("google_login")}?next=%2F"'
        )

    def test_home_shows_username_without_email(self):
        user = User.objects.create_user(username="noemail", password="12345")
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "You are signed in as <u>noemail</u>")


# Tests user creation, login, and logout
class UserAuthenticationTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="12345")

    def test_login_logout(self):
        # Simulate user login
        self.client.force_login(self.user)
        self.assertTrue(self.user.is_authenticated)

        # A GET only shows the logout confirmation page
        response = self.client.get(reverse("account_logout"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Test user logout
        response = self.client.post(reverse("account_logout"))

        # Check if the user is logged out
        self.assertFalse(response.wsgi_request.user.is_authenticated)


# Tests if adding and removing a list works
class AddListTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="12345")

    def test_add_list(self):
        # Login the test user
        self.client.login(username="testuser", password="12345")

        # Count the initial number of lists
        initial_count = List.objects.count()

        # Post request to add a new list
        response = self.client.post(reverse("add_list"), {"list_name": "Test List"})

        # Check if the request was successful and redirected to the correct URL
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("lists_index"))

        # Check if the list was added to the database
        self.assertEqual(List.objects.count(), initial_count + 1)
        new_list = List.objects.last()
        self.assertEqual(new_list.list_name, "Test List")
        self.assertEqual(new_list.user_id, self.user)

        # Test removal of list
        List.objects.filter(list_name="Test List").delete()

        # Check if list was removed from the database
        self.assertEqual(List.objects.count(), initial_count)

        # Log the user out
        self.client.logout()


# Testing if adding and removing an item works
class AddItemTest(TestCase):
    def setUp(self):
        # Create objects for test
        self.user = User.objects.create_user(username="testuser", password="12345")

        self.list = List.objects.create(user_id=self.user, list_name="Test List")

    def test_add_item(self):
        # Count the initial number of items
        initial_count = Item.objects.count()

        # Log in the user (if needed)
        self.client.login(username="testuser", password="12345")

        # Simulate adding an item
        response = self.client.post(
            f"/add/{self.list.id}/", {"item_descr": "Test Item"}
        )

        # Check if the item was added successfully (redirects to list view)
        self.assertEqual(response.status_code, 302)

        # Check if the number of items increased by 1
        self.assertEqual(Item.objects.count(), initial_count + 1)

        # Get the added item
        added_item = Item.objects.latest("item_date_added")

        # Check if the added item belongs to the correct list
        self.assertEqual(added_item.list_id, self.list)

        # Check if the item description is correct
        self.assertEqual(added_item.item_descr, "Test Item")

        # Check if the item is not done by default
        self.assertFalse(added_item.item_done)

        # Remove the item
        Item.objects.filter(item_descr="Test Item").delete()

        # Check if the item is removed correctly
        self.assertEqual(Item.objects.count(), initial_count)

        # Log the user out
        self.client.logout()


class ItemDoneTest(TestCase):
    def setUp(self):
        # Create objects for test
        self.user = User.objects.create_user(username="testuser", password="12345")

        self.list = List.objects.create(user_id=self.user, list_name="Test List")

        self.item = Item.objects.create(
            list_id=self.list,
            item_date_added=timezone.now(),
            item_descr="Test Item",
            item_done=False,
        )

        self.client = Client()

    def test_item_done(self):
        # Log in the user (if needed)
        self.client.login(username="testuser", password="12345")

        # Mark the item as done
        response = self.client.post(
            reverse("item_done", kwargs={"item_id": self.item.id})
        )

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
        self.user = User.objects.create_user(username="testuser", password="12345")

        self.list = List.objects.create(user_id=self.user, list_name="Test List")

        self.item1 = Item.objects.create(
            list_id=self.list,
            item_descr="Item 1",
            item_done=False,
            item_date_added=timezone.now(),
        )
        self.item2 = Item.objects.create(
            list_id=self.list,
            item_descr="Item 2",
            item_done=True,
            item_date_added=timezone.now(),
        )

        self.client = Client()

    def test_list_view(self):
        # Log in the user
        self.client.login(username="testuser", password="12345")

        # Make a GET request to the list view
        response = self.client.get(
            reverse("list_view", kwargs={"list_id": self.list.id})
        )

        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Check if the correct list is being passed to the template
        self.assertEqual(response.context["list_obj"], self.list)

        # Check if the correct items are being passed to the template and are sorted by default
        expected_items = [self.item1, self.item2]
        actual_items = list(response.context["list_items"])
        self.assertEqual(expected_items, actual_items)

        # Logging the user out
        self.client.logout()


class ItemDetailsTest(TestCase):
    def setUp(self):
        # Create objects for test
        self.user = User.objects.create_user(username="testuser", password="12345")

        self.list = List.objects.create(user_id=self.user, list_name="Test List")

        self.item = Item.objects.create(
            list_id=self.list,
            item_date_added=timezone.now(),
            item_descr="Test Item",
            item_done=False,
        )

        self.client = Client()

    def test_item_details(self):
        # Logging the user in
        self.client.login(username="testuser", password="12345")

        # Grabbing the item details
        response = self.client.post(
            reverse("item_details", kwargs={"item_id": self.item.id})
        )

        # Check if the status code is 200
        self.assertEqual(response.status_code, 200)

        # Check if the right details are given based on the response's context
        self.assertEqual(response.context["item"], self.item)
        self.assertEqual(response.context["list_name"], self.list.list_name)

        # Logging the user out
        self.client.logout()


# Tests that one user can't see or change another user's lists and items
class OwnershipTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="12345")
        self.other_user = User.objects.create_user(username="other", password="12345")
        self.list = List.objects.create(user_id=self.owner, list_name="Owner's List")
        self.item = Item.objects.create(
            list_id=self.list,
            item_date_added=timezone.now(),
            item_descr="Owner's Item",
            item_done=False,
        )
        self.client.force_login(self.other_user)

    def test_other_user_gets_404_on_views(self):
        for url in [
            reverse("list_view", kwargs={"list_id": self.list.id}),
            reverse("item_details", kwargs={"item_id": self.item.id}),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_other_user_gets_404_on_changes(self):
        for url, data in [
            (reverse("item_done", kwargs={"item_id": self.item.id}), {}),
            (
                reverse("add_item", kwargs={"list_id": self.list.id}),
                {"item_descr": "Intruder's Item"},
            ),
            (reverse("delete_item", kwargs={"item_id": self.item.id}), {}),
            (reverse("delete_list", kwargs={"list_id": self.list.id}), {}),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, data).status_code, 404)

        # Nothing changed in the database
        self.item.refresh_from_db()
        self.assertFalse(self.item.item_done)
        self.assertEqual(list(Item.objects.all()), [self.item])
        self.assertEqual(list(List.objects.all()), [self.list])


# Tests that data only changes on POST
class PostOnlyTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.list = List.objects.create(user_id=self.user, list_name="Test List")
        self.item = Item.objects.create(
            list_id=self.list,
            item_date_added=timezone.now(),
            item_descr="Test Item",
            item_done=False,
        )
        self.mutating_urls = [
            reverse("item_done", kwargs={"item_id": self.item.id}),
            reverse("add_item", kwargs={"list_id": self.list.id}),
            reverse("add_list"),
            reverse("delete_item", kwargs={"item_id": self.item.id}),
            reverse("delete_list", kwargs={"list_id": self.list.id}),
        ]

    def test_get_returns_405(self):
        self.client.force_login(self.user)
        for url in self.mutating_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)

        # Nothing changed in the database
        self.item.refresh_from_db()
        self.assertFalse(self.item.item_done)
        self.assertEqual(list(Item.objects.all()), [self.item])
        self.assertEqual(list(List.objects.all()), [self.list])

    def test_logged_out_post_redirects_to_login(self):
        for url in self.mutating_urls:
            with self.subTest(url=url):
                response = self.client.post(url)
                self.assertRedirects(
                    response,
                    f"{reverse('account_login')}?next={url}",
                    fetch_redirect_response=False,
                )


# Tests that bad list names and item descriptions are rejected without a crash
class ValidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.list = List.objects.create(user_id=self.user, list_name="Test List")
        self.client.force_login(self.user)

    def test_bad_list_names_are_rejected(self):
        for data, message in [
            ({"list_name": ""}, "Enter a list name."),
            ({"list_name": "   "}, "Enter a list name."),
            ({}, "Enter a list name."),
            ({"list_name": "x" * 201}, "at most 200 characters (this one has 201)"),
        ]:
            with self.subTest(data=data):
                response = self.client.post(reverse("add_list"), data, follow=True)
                self.assertRedirects(response, reverse("lists_index"))
                self.assertContains(response, message)
        self.assertEqual(list(List.objects.all()), [self.list])

    def test_bad_item_descriptions_are_rejected(self):
        list_url = reverse("list_view", kwargs={"list_id": self.list.id})
        add_url = reverse("add_item", kwargs={"list_id": self.list.id})
        for data, message in [
            ({"item_descr": ""}, "Enter an item description."),
            ({"item_descr": "   "}, "Enter an item description."),
            ({}, "Enter an item description."),
            ({"item_descr": "x" * 201}, "at most 200 characters (this one has 201)"),
        ]:
            with self.subTest(data=data):
                response = self.client.post(add_url, data, follow=True)
                self.assertRedirects(response, list_url)
                self.assertContains(response, message)
        self.assertFalse(Item.objects.exists())

    def test_names_are_stripped(self):
        self.client.post(reverse("add_list"), {"list_name": "  Groceries  "})
        self.client.post(
            reverse("add_item", kwargs={"list_id": self.list.id}),
            {"item_descr": "  Milk  "},
        )
        self.assertTrue(List.objects.filter(list_name="Groceries").exists())
        item = Item.objects.get(item_descr="Milk")
        self.assertFalse(item.item_done)
        self.assertIsNotNone(item.item_date_added)
