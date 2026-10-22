from datetime import datetime, timedelta

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


# Tests each sort option, the fallback for unknown options, and the selected option
class SortingTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.force_login(self.user)

        self.list = List.objects.create(user_id=self.user, list_name="Work")
        groceries = List.objects.create(user_id=self.user, list_name="Groceries")
        chores = List.objects.create(user_id=self.user, list_name="Chores")
        self.lists_by_creation = [self.list, groceries, chores]
        other_user = User.objects.create_user(username="other", password="12345")
        List.objects.create(user_id=other_user, list_name="Another user's list")

        # "Banana" and "Date" share a date, so the order between them comes from the id
        now = timezone.now()
        self.cherry = self.make_item("Cherry", now - timedelta(days=2), done=True)
        self.apple = self.make_item("Apple", now, done=False)
        self.banana = self.make_item("Banana", now - timedelta(days=1), done=False)
        self.date = self.make_item("Date", now - timedelta(days=1), done=True)

    def make_item(self, description: str, date_added: datetime, done: bool) -> Item:
        return Item.objects.create(
            list_id=self.list,
            item_descr=description,
            item_date_added=date_added,
            item_done=done,
        )

    def get_items(self, query: dict[str, str]) -> list[Item]:
        url = reverse("list_view", kwargs={"list_id": self.list.id})
        return list(self.client.get(url, query).context["list_items"])

    def test_item_sort_orders(self):
        oldest_first = [self.cherry, self.banana, self.date, self.apple]
        for query, expected in [
            ({}, oldest_first),
            ({"sort": "normal"}, oldest_first),
            ({"sort": "unknown"}, oldest_first),
            ({"sort": "date_added"}, [self.apple, self.date, self.banana, self.cherry]),
            (
                {"sort": "description"},
                [self.apple, self.banana, self.cherry, self.date],
            ),
            ({"sort": "completed"}, [self.banana, self.apple, self.cherry, self.date]),
        ]:
            with self.subTest(query=query):
                self.assertEqual(self.get_items(query), expected)

    def test_list_sort_orders(self):
        work, groceries, chores = self.lists_by_creation
        for query, expected in [
            ({}, [work, groceries, chores]),
            ({"sort": "oldToNew"}, [work, groceries, chores]),
            ({"sort": "unknown"}, [work, groceries, chores]),
            ({"sort": "list_name"}, [chores, groceries, work]),
        ]:
            with self.subTest(query=query):
                response = self.client.get(reverse("lists_index"), query)
                self.assertEqual(list(response.context["lists"]), expected)

    def test_selected_option_stays_selected(self):
        list_url = reverse("list_view", kwargs={"list_id": self.list.id})
        for url, query, selected in [
            (list_url, {}, "normal"),
            (list_url, {"sort": "description"}, "description"),
            (list_url, {"sort": "unknown"}, "normal"),
            (reverse("lists_index"), {}, "oldToNew"),
            (reverse("lists_index"), {"sort": "list_name"}, "list_name"),
        ]:
            with self.subTest(url=url, query=query):
                response = self.client.get(url, query)
                self.assertContains(response, f'<option value="{selected}" selected>')
                self.assertContains(response, " selected>", count=1)


# Tests that adding, toggling and deleting keep the page's current sort
class KeepSortTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.force_login(self.user)
        self.list = List.objects.create(user_id=self.user, list_name="Test List")
        self.list_url = reverse("list_view", kwargs={"list_id": self.list.id})

    def make_item(self) -> Item:
        return Item.objects.create(list_id=self.list, item_descr="Test Item")

    def test_item_changes_keep_the_sort(self):
        for sort, expected_url in [
            ("description", f"{self.list_url}?sort=description"),
            ("normal", self.list_url),
            ("unknown", self.list_url),
        ]:
            for url, data in [
                (
                    reverse("add_item", kwargs={"list_id": self.list.id}),
                    {"item_descr": "New Item"},
                ),
                (reverse("add_item", kwargs={"list_id": self.list.id}), {}),
                (reverse("item_done", kwargs={"item_id": self.make_item().id}), {}),
                (reverse("delete_item", kwargs={"item_id": self.make_item().id}), {}),
            ]:
                with self.subTest(sort=sort, url=url, data=data):
                    response = self.client.post(url, {**data, "sort": sort})
                    self.assertRedirects(
                        response, expected_url, fetch_redirect_response=False
                    )

    def test_list_changes_keep_the_sort(self):
        lists_url = reverse("lists_index")
        for sort, expected_url in [
            ("list_name", f"{lists_url}?sort=list_name"),
            ("oldToNew", lists_url),
        ]:
            other_list = List.objects.create(user_id=self.user, list_name="Other")
            for url, data in [
                (reverse("add_list"), {"list_name": "New List"}),
                (reverse("add_list"), {}),
                (reverse("delete_list", kwargs={"list_id": other_list.id}), {}),
            ]:
                with self.subTest(sort=sort, url=url, data=data):
                    response = self.client.post(url, {**data, "sort": sort})
                    self.assertRedirects(
                        response, expected_url, fetch_redirect_response=False
                    )

    def test_forms_post_the_current_sort(self):
        self.make_item()
        response = self.client.get(self.list_url, {"sort": "completed"})
        # Add, toggle and delete forms
        self.assertContains(
            response, '<input type="hidden" name="sort" value="completed">', count=3
        )
        response = self.client.get(reverse("lists_index"), {"sort": "list_name"})
        # Add and delete forms
        self.assertContains(
            response, '<input type="hidden" name="sort" value="list_name">', count=2
        )
