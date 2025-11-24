
from enum import Enum


class MusicPack:
    id: int
    human_name: str
    name: str
    cost: int  # в копейках
    file_name: str
    description: str
    track_count: int

    def __init__(self, id: int, human_name: str, cost: int, file_name: str, description: str, track_count: int):
        '''cost указывается и сохраняется в копейках'''
        self.human_name = human_name
        self.cost = cost
        self.file_name = file_name
        self.name = self.human_name.lower().replace(" ", "_")
        self.description = description
        self.track_count = track_count


class Categories(Enum):
    DnB = "Drum&Base"
    House = "House"


DNB_packs: list = [
    MusicPack(1, "Drum&Base 50", 5000*100, "ДНБ 50.zip",
              "Drum&base pack, в котором собраны треки из всех поджанров",
              50),
    MusicPack(2, "Drum&Base 30", 3000*100, "ДНБ 30.zip",
              "Drum&base pack, в котором собраны треки из всех поджанров", 30)
]

HOUSE_packs: list = [
    MusicPack(3, "House 30", 3000*100, "Хаус 30.zip", "", 30),
    MusicPack(4, "House 50", 5000*100, "Хаус 50.zip", "", 50)

]

Categories_dict = {Categories.DnB.value: {p.name: p for p in DNB_packs},
                   Categories.House.value: {p.name: p for p in HOUSE_packs}}


def get_pack_by_name_or_category(pack_or_category_name: str) -> MusicPack | dict[str, MusicPack] | None:
    if pack_or_category_name in Categories_dict:
        return Categories_dict.get(pack_or_category_name)
    for cat_name, packs_dict in Categories_dict.items():
        if pack_or_category_name in packs_dict:
            return packs_dict.get(pack_or_category_name)


def get_pack_price(pack_name: str | None):
    if pack_name:
        pack: MusicPack = get_pack_by_name_or_category(pack_name)
        if pack and isinstance(pack, MusicPack):
            return pack.cost
    return 0
