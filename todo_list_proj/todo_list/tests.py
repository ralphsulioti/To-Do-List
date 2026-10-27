from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
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


class HomePageTest(TestCase):
    @override_settings(
        GOOGLE_LOGIN_ENABLED=False, SOCIALACCOUNT_PROVIDERS=GOOGLE_PROVIDER_WITHOUT_APP
    )
    def test_home_without_google(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("account_login"))
        self.assertContains(response, reverse("account_signup"))
        self.assertNotContains(response, "Sign in with Google")

    @override_settings(
        GOOGLE_LOGIN_ENABLED=True, SOCIALACCOUNT_PROVIDERS=GOOGLE_PROVIDER_WITH_APP
    )
    def test_home_with_google(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in with Google")
        self.assertContains(
            response, f'method="post" action="{reverse("google_login")}?next=%2F"'
        )

    def test_home_shows_username_without_email(self):
        user = User.objects.create_user(username="noemail", password="12345")
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Signed in as <strong>noemail</strong>")

    def test_account_pages_use_the_app_layout(self):
        response = self.client.get(reverse("account_login"))

        self.assertContains(response, 'class="card shadow-sm auth-card')
        self.assertContains(response, 'class="form-label"')


class LogoutTest(TestCase):
    def test_only_post_logs_out(self):
        user = User.objects.create_user(username="testuser", password="12345")
        self.client.force_login(user)

        # A GET only shows allauth's confirmation page
        response = self.client.get(reverse("account_logout"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        response = self.client.post(reverse("account_logout"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class OwnerActionsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.list = List.objects.create(user=self.user, list_name="Test List")
        self.client.force_login(self.user)

    def test_add_and_delete_list(self):
        self.client.post(reverse("add_list"), {"list_name": "Groceries"})
        new_list = List.objects.get(list_name="Groceries")
        self.assertEqual(new_list.user, self.user)

        self.client.post(reverse("delete_list", kwargs={"list_id": new_list.id}))
        self.assertFalse(List.objects.filter(pk=new_list.id).exists())

    def test_add_toggle_and_delete_item(self):
        self.client.post(
            reverse("add_item", kwargs={"list_id": self.list.id}),
            {"item_descr": "Milk"},
        )
        item = Item.objects.get(item_descr="Milk")
        self.assertEqual(item.list, self.list)
        self.assertFalse(item.item_done)

        toggle_url = reverse("item_done", kwargs={"item_id": item.id})
        for expected_done in [True, False]:
            self.client.post(toggle_url)
            item.refresh_from_db()
            self.assertEqual(item.item_done, expected_done)

        self.client.post(reverse("delete_item", kwargs={"item_id": item.id}))
        self.assertFalse(Item.objects.filter(pk=item.id).exists())

    def test_item_details(self):
        item = Item.objects.create(list=self.list, item_descr="Milk")

        response = self.client.get(reverse("item_details", kwargs={"item_id": item.id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["item"], item)
        self.assertEqual(response.context["list_name"], self.list.list_name)


class OwnershipTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="12345")
        self.other_user = User.objects.create_user(username="other", password="12345")
        self.list = List.objects.create(user=self.owner, list_name="Owner's List")
        self.item = Item.objects.create(list=self.list, item_descr="Owner's Item")
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

        self.item.refresh_from_db()
        self.assertFalse(self.item.item_done)
        self.assertEqual(list(Item.objects.all()), [self.item])
        self.assertEqual(list(List.objects.all()), [self.list])


class PostOnlyTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.list = List.objects.create(user=self.user, list_name="Test List")
        self.item = Item.objects.create(list=self.list, item_descr="Test Item")
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


class ValidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.list = List.objects.create(user=self.user, list_name="Test List")
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
        self.assertTrue(Item.objects.filter(item_descr="Milk").exists())


class SortingTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.force_login(self.user)

        self.list = List.objects.create(user=self.user, list_name="Work")
        groceries = List.objects.create(user=self.user, list_name="Groceries")
        chores = List.objects.create(user=self.user, list_name="Chores")
        self.lists_by_creation = [self.list, groceries, chores]
        other_user = User.objects.create_user(username="other", password="12345")
        List.objects.create(user=other_user, list_name="Another user's list")

        # "Banana" and "Date" share a date, so the order between them comes from the id
        now = timezone.now()
        self.cherry = self.make_item("Cherry", now - timedelta(days=2), done=True)
        self.apple = self.make_item("Apple", now, done=False)
        self.banana = self.make_item("Banana", now - timedelta(days=1), done=False)
        self.date = self.make_item("Date", now - timedelta(days=1), done=True)

    def make_item(self, description: str, date_added: datetime, done: bool) -> Item:
        return Item.objects.create(
            list=self.list,
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


class KeepSortTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.force_login(self.user)
        self.list = List.objects.create(user=self.user, list_name="Test List")
        self.list_url = reverse("list_view", kwargs={"list_id": self.list.id})

    def make_item(self) -> Item:
        return Item.objects.create(list=self.list, item_descr="Test Item")

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
            other_list = List.objects.create(user=self.user, list_name="Other")
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
