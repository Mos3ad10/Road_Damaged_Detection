import argparse
import random
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


# RDD2022 road damage classes used for bounding-box object detection.
CLASS_MAP = {
    "D00": 0,  # longitudinal crack
    "D10": 1,  # transverse crack
    "D20": 2,  # alligator crack
    "D40": 3,  # pothole
}

CLASS_NAMES = [
    "D00_longitudinal_crack",
    "D10_transverse_crack",
    "D20_alligator_crack",
    "D40_pothole",
]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def safe_extract_zip(zip_path, destination, strip_first_folder=True):
    """
    Extract a zip safely.

    Example:
        United_States/train/images/...

    becomes:
        extracted/United_States/train/images/...
    """
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue

            parts = Path(member.filename).parts
            if not parts:
                continue

            if strip_first_folder and len(parts) > 1:
                parts = parts[1:]

            output_path = destination.joinpath(*parts).resolve()
            destination_resolved = destination.resolve()

            if not str(output_path).startswith(str(destination_resolved)):
                raise RuntimeError(f"Unsafe zip path blocked: {member.filename}")

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, output_path.open("wb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)


def extract_inner_country_zips(parent_zip, temp_zip_dir):
    """
    Extract country zip files from the main RDD2022 zip.

    The original big zip is kept safe. Only the copied country zips inside
    temp_zip_dir are deleted after extraction.
    """
    temp_zip_dir.mkdir(parents=True, exist_ok=True)
    country_zips = []

    with zipfile.ZipFile(parent_zip) as archive:
        for member in archive.infolist():
            if not member.filename.lower().endswith(".zip"):
                continue

            country_zip_path = temp_zip_dir / Path(member.filename).name
            print(f"Copying inner zip: {member.filename}")

            with archive.open(member) as source, country_zip_path.open("wb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)

            country_zips.append(country_zip_path)

    return country_zips


def get_zip_mode(zip_path):
    """Return 'parent' if the zip contains country zip files, otherwise 'country'."""
    with zipfile.ZipFile(zip_path) as archive:
        has_inner_zips = any(member.filename.lower().endswith(".zip") for member in archive.infolist())
    return "parent" if has_inner_zips else "country"


def prepare_country_folders(source, output_root, delete_source_zips=False):
    """
    Create one extracted folder per country zip.

    Supported source values:
    - Main RDD2022 zip containing country zips.
    - A folder containing country zip files.
    - One country zip file.
    - A folder that already has extracted country folders.
    """
    source = Path(source).expanduser().resolve()
    output_root = Path(output_root).expanduser().resolve()
    extracted_root = output_root / "extracted"
    temp_zip_dir = output_root / "_temporary_country_zips"

    extracted_root.mkdir(parents=True, exist_ok=True)

    zips_to_extract = []
    delete_after_extract = set()

    if source.is_file() and source.suffix.lower() == ".zip":
        mode = get_zip_mode(source)
        if mode == "parent":
            zips_to_extract = extract_inner_country_zips(source, temp_zip_dir)
            delete_after_extract.update(zips_to_extract)
        else:
            zips_to_extract = [source]
            if delete_source_zips:
                delete_after_extract.add(source)

    elif source.is_dir():
        # Look only at zip files directly inside SOURCE_PATH. This avoids picking up
        # temporary or unrelated nested zip files on repeated notebook runs.
        zips_to_extract = sorted(source.glob("*.zip"))
        if delete_source_zips:
            delete_after_extract.update(zips_to_extract)

    else:
        raise FileNotFoundError(f"Source does not exist or is not supported: {source}")

    if not zips_to_extract:
        existing_country_folders = sorted(
            folder for folder in extracted_root.iterdir()
            if folder.is_dir() and any(folder.rglob("train/annotations/xmls"))
        )
        if existing_country_folders:
            print("No country zip files found. Using already extracted country folders.")
            return existing_country_folders
        raise RuntimeError("No zip files or extracted country folders found.")

    country_folders = []
    for zip_file in zips_to_extract:
        country_name = zip_file.stem
        country_folder = extracted_root / country_name

        print(f"\nExtracting {zip_file.name} -> {country_folder}")
        safe_extract_zip(zip_file, country_folder, strip_first_folder=True)
        country_folders.append(country_folder)

        if zip_file in delete_after_extract and zip_file.exists():
            zip_file.unlink()
            print(f"Deleted zip after extraction: {zip_file}")

    if temp_zip_dir.exists() and not any(temp_zip_dir.iterdir()):
        temp_zip_dir.rmdir()

    return country_folders


def voc_box_to_yolo(box, image_width, image_height):
    xmin = max(0.0, float(box.findtext("xmin")))
    ymin = max(0.0, float(box.findtext("ymin")))
    xmax = min(float(image_width), float(box.findtext("xmax")))
    ymax = min(float(image_height), float(box.findtext("ymax")))

    box_width = xmax - xmin
    box_height = ymax - ymin

    x_center = (xmin + box_width / 2.0) / image_width
    y_center = (ymin + box_height / 2.0) / image_height
    box_width = box_width / image_width
    box_height = box_height / image_height

    return x_center, y_center, box_width, box_height


def convert_xml_to_yolo(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    size = root.find("size")
    image_width = int(size.findtext("width"))
    image_height = int(size.findtext("height"))
    image_filename = root.findtext("filename")

    yolo_rows = []
    ignored_classes = {}

    for obj in root.findall("object"):
        class_name = (obj.findtext("name") or "").strip()
        if class_name not in CLASS_MAP:
            ignored_classes[class_name] = ignored_classes.get(class_name, 0) + 1
            continue

        box = obj.find("bndbox")
        x_center, y_center, box_width, box_height = voc_box_to_yolo(
            box,
            image_width,
            image_height,
        )

        if box_width <= 0 or box_height <= 0:
            continue

        class_id = CLASS_MAP[class_name]
        yolo_rows.append(
            f"{class_id} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}"
        )

    return image_filename, yolo_rows, ignored_classes


def find_train_images_and_xmls(country_folder):
    train_images_dir = next(country_folder.rglob("train/images"), None)
    train_xml_dir = next(country_folder.rglob("train/annotations/xmls"), None)

    if train_images_dir is None or train_xml_dir is None:
        print(f"Skipped {country_folder.name}: train/images or train/annotations/xmls not found.")
        return []

    image_by_stem = {
        image_path.stem: image_path
        for image_path in train_images_dir.iterdir()
        if image_path.suffix.lower() in IMAGE_EXTENSIONS
    }

    items = []
    for xml_path in sorted(train_xml_dir.glob("*.xml")):
        image_filename, yolo_rows, ignored_classes = convert_xml_to_yolo(xml_path)

        image_path = None
        if image_filename:
            candidate = train_images_dir / image_filename
            if candidate.exists():
                image_path = candidate

        if image_path is None:
            image_path = image_by_stem.get(xml_path.stem)

        if image_path is None:
            print(f"Warning: image not found for {xml_path.name}")
            continue

        items.append(
            {
                "country": country_folder.name,
                "image_path": image_path,
                "label_rows": yolo_rows,
                "ignored_classes": ignored_classes,
            }
        )

    return items


def split_items(items, train_ratio, val_ratio, seed):
    if train_ratio + val_ratio >= 1.0:
        raise ValueError("train_ratio + val_ratio must be less than 1.0")

    shuffled = list(items)
    random.Random(seed).shuffle(shuffled)

    train_end = int(len(shuffled) * train_ratio)
    val_end = train_end + int(len(shuffled) * val_ratio)

    return {
        "train": shuffled[:train_end],
        "val": shuffled[train_end:val_end],
        "test": shuffled[val_end:],
    }


def copy_yolo_dataset(splits, yolo_root):
    for split_name in ["train", "val", "test"]:
        (yolo_root / "images" / split_name).mkdir(parents=True, exist_ok=True)
        (yolo_root / "labels" / split_name).mkdir(parents=True, exist_ok=True)

    for split_name, items in splits.items():
        for item in items:
            source_image = item["image_path"]

            # Prefix with country name to avoid filename collisions between subsets.
            output_name = f"{item['country']}_{source_image.name}"
            output_image = yolo_root / "images" / split_name / output_name
            output_label = yolo_root / "labels" / split_name / f"{Path(output_name).stem}.txt"

            shutil.copy2(source_image, output_image)
            output_label.write_text(
                "\n".join(item["label_rows"]) + ("\n" if item["label_rows"] else ""),
                encoding="utf-8",
            )


def write_data_yaml(yolo_root):
    yaml_text = "\n".join(
        [
            f"path: {yolo_root.as_posix()}",
            "train: images/train",
            "val: images/val",
            "test: images/test",
            "names:",
            *[f"  {class_id}: {class_name}" for class_id, class_name in enumerate(CLASS_NAMES)],
            "",
        ]
    )

    (yolo_root / "data.yaml").write_text(yaml_text, encoding="utf-8")


def yolo_split_dirs_exist(yolo_root):
    required_dirs = [
        yolo_root / "images" / "train",
        yolo_root / "images" / "val",
        yolo_root / "images" / "test",
        yolo_root / "labels" / "train",
        yolo_root / "labels" / "val",
        yolo_root / "labels" / "test",
    ]
    return all(path.is_dir() for path in required_dirs)


def yolo_labels_match_images(yolo_root):
    for split_name in ["train", "val", "test"]:
        image_dir = yolo_root / "images" / split_name
        label_dir = yolo_root / "labels" / split_name
        image_stems = {
            path.stem
            for path in image_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        }
        label_stems = {
            path.stem
            for path in label_dir.glob("*.txt")
            if path.is_file()
        }
        if not image_stems.issubset(label_stems):
            return False
    return True


def yolo_dataset_ready(yolo_root):
    return (
        (yolo_root / "data.yaml").is_file()
        and yolo_split_dirs_exist(yolo_root)
        and yolo_labels_match_images(yolo_root)
    )


def convert_rdd2022_to_yolo(country_folders, output_root, train_ratio, val_ratio, seed, force=False):
    yolo_root = Path(output_root) / "RDD2022_YOLO"
    if yolo_root.exists():
        if yolo_dataset_ready(yolo_root) and not force:
            print(f"Using existing YOLO dataset folder: {yolo_root}")
            return yolo_root

        if yolo_split_dirs_exist(yolo_root) and yolo_labels_match_images(yolo_root) and not force:
            write_data_yaml(yolo_root)
            print(f"Repaired missing data.yaml for existing YOLO dataset: {yolo_root / 'data.yaml'}")
            return yolo_root

        if not force:
            raise FileExistsError(
                f"YOLO dataset folder already exists but is incomplete: {yolo_root}. "
                "Delete it manually or call convert_rdd2022_to_yolo(..., force=True) to rebuild it. "
                "Expected data.yaml, split folders, and one .txt label for every image."
            )

        print(f"\nRemoving old YOLO dataset folder: {yolo_root}")
        shutil.rmtree(yolo_root)

    all_items = []
    ignored_total = {}

    for country_folder in country_folders:
        items = find_train_images_and_xmls(country_folder)
        print(f"{country_folder.name}: {len(items)} labeled images found")
        all_items.extend(items)

        for item in items:
            for class_name, count in item["ignored_classes"].items():
                ignored_total[class_name] = ignored_total.get(class_name, 0) + count

    if not all_items:
        raise RuntimeError("No labeled images found. Check the extracted folder structure.")

    splits = split_items(all_items, train_ratio, val_ratio, seed)

    print("\nCreating YOLO dataset with split:")
    print(f"Train: {train_ratio:.0%}")
    print(f"Val:   {val_ratio:.0%}")
    print(f"Test:  {1 - train_ratio - val_ratio:.0%}")
    copy_yolo_dataset(splits, yolo_root)
    write_data_yaml(yolo_root)

    print("\nFinished.")
    print(f"YOLO dataset folder: {yolo_root}")
    print(f"Train images: {len(splits['train'])}")
    print(f"Val images:   {len(splits['val'])}")
    print(f"Test images:  {len(splits['test'])}")
    print(f"data.yaml:    {yolo_root / 'data.yaml'}")

    if ignored_total:
        print(f"Ignored classes: {ignored_total}")

    return yolo_root


def main():
    parser = argparse.ArgumentParser(
        description="Extract RDD2022 country zip files and convert Pascal VOC XML annotations to YOLO format."
    )
    parser.add_argument(
        "--source",
        default=r"C:\Users\MOS3AD\Downloads\RDD2022_released_through_CRDDC2022 (2).zip",
        help="Main RDD2022 zip, one country zip, or a folder containing country zips.",
    )
    parser.add_argument(
        "--output",
        default=r"D:\CV_INSTANT\Project 2\RDD2022",
        help="Output folder for extracted countries and YOLO dataset.",
    )
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--delete-source-zips",
        action="store_true",
        help="Delete source country zip files after extraction. The main parent zip is never deleted automatically.",
    )
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Delete and recreate RDD2022_YOLO if it already exists.",
    )
    args = parser.parse_args()

    output_root = Path(args.output).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    country_folders = prepare_country_folders(
        source=args.source,
        output_root=output_root,
        delete_source_zips=args.delete_source_zips,
    )

    convert_rdd2022_to_yolo(
        country_folders=country_folders,
        output_root=output_root,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        seed=args.seed,
        force=args.force_rebuild,
    )


if __name__ == "__main__":
    main()
