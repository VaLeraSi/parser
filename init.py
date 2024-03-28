import collections

ParseResult = collections.namedtuple(
    "ParseResult",
    (
        "id",
        "name",
        "brand",
        "url",
        "price",
        "promo_price",
    ),
)

HEADERS = (
    "ID",
    "Наименование товара",
    "Бренд",
    "Ссылка",
    "Цена",
    "ПРОМО цена",
)
