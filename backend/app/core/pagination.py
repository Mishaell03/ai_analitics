from dataclasses import dataclass

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

@dataclass(frozen=True)
class Pagination:
    page: int
    page_size: int
    offset: int

def get_pagination(
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Pagination:
    if page < 1:
        page = DEFAULT_PAGE

    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE
    elif page_size > MAX_PAGE_SIZE:
        page_size = MAX_PAGE_SIZE

    offset = (page - 1) * page_size

    return Pagination(
        page=page,
        page_size=page_size,
        offset=offset,
    )


def get_total_pages(
    total: int,
    page_size: int,
) -> int:
    if total <= 0:
        return 0

    return (total + page_size - 1) // page_size