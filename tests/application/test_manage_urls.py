import pytest

from healthchecker.application.use_cases.manage_urls import ManageUrlsUseCase
from healthchecker.domain.models.url import Url


class TestManageUrlsUseCase:
    @pytest.fixture
    def mock_repo(self, mocker):
        repo = mocker.AsyncMock()

        async def add_side_effect(url: Url) -> Url:
            url.id = 1
            return url

        repo.add.side_effect = add_side_effect
        repo.get_all_active.return_value = [
            Url(
                id=1,
                name="Example",
                url="https://example.com",
                alert_before_days=30,
                is_active=True,
                created_at=None,
                updated_at=None,
            ),
        ]
        repo.get_by_id.return_value = Url(
            id=1,
            name="Example",
            url="https://example.com",
            alert_before_days=30,
            is_active=True,
            created_at=None,
            updated_at=None,
        )
        return repo

    @pytest.fixture
    def use_case(self, mock_repo):
        return ManageUrlsUseCase(mock_repo)

    async def test_add_url(self, use_case, mock_repo):
        result = await use_case.add("https://example.com", "Example", 14)
        mock_repo.add.assert_awaited_once()
        assert result.name == "Example"
        assert result.alert_before_days == 14

    async def test_add_url_defaults(self, use_case, mock_repo):
        result = await use_case.add("https://example.com")
        assert result.name == "https://example.com"
        assert result.alert_before_days == 30

    async def test_list_all(self, use_case, mock_repo):
        result = await use_case.list_all()
        mock_repo.get_all_active.assert_awaited_once()
        assert len(result) == 1

    async def test_delete(self, use_case, mock_repo):
        await use_case.delete(1)
        mock_repo.delete.assert_awaited_once_with(1)

    async def test_get_by_id(self, use_case, mock_repo):
        result = await use_case.get_by_id(1)
        mock_repo.get_by_id.assert_awaited_once_with(1)
        assert result is not None
        assert result.id == 1
