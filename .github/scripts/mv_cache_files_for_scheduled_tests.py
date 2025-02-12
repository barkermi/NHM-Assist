import pathlib as pl
import shutil

repo_dir = pl.Path("../../").resolve()
tmp_path = repo_dir / "tmp_relocation_of_output"
nb_output_dir = repo_dir / "domain_data/willamette_river/notebook_output_files"
nc_files_path = nb_output_dir / "nc_files"
paths_to_mv = {
    "owrd_cache.nc": (nc_files_path, tmp_path),
    "sf_efc.nc": (nc_files_path, tmp_path),
    "Folium_maps": (nb_output_dir, tmp_path),
}


def relocate_path(name: str, from_dir: pl.Path, to_dir: pl.Path, force=True):
    """Move a file from one directory to another.

    Args:
      name: the name of the file as a string.
      from_dir: the pathlib.Path of the source directory.
      to_dir: the pathlib.Path of the destination directory.
      force: bool if the destination is to be discarded.
    """
    src = from_dir / name
    dst = to_dir / name

    if dst.exists():
        if not force:
            msg = f"Destionation file exists and force=False: {dst}"
            raise FileExistsError()
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()

    src.rename(dst)
    assert dst.exists()
    assert not src.exists()
    print(f"relocated {str(src)} -> {str(dst)}")

    return


def mv_cache_files_for_scheduled_tests():
    if not tmp_path.exists():
        tmp_path.mkdir()
    for key, val in paths_to_mv.items():
        relocate_path(key, val[0], val[1])

    return


def restore_cache_files_after_scheduled_tests():
    for key, val in paths_to_mv.items():
        relocate_path(key, val[1], val[0])

    shutil.rmtree(tmp_path)

    return


if __name__ == "__main__":
    mv_cache_files_for_scheduled_tests()
