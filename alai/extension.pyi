

class Package:
    @property
    def name(self) -> str: ...

    @property
    def depends(self) -> list[str]: ...

def find_package(arg: str, /) -> Package | None: ...
