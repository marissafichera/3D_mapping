import os
import rasterio
from numpy import array, dstack


def get_surface(p):
    """
​
    p = path to tiff
    return a numpy array
​
    in practice array made by rasterio.
    here for demo going to return a simple 2d array
    """
    dataset = rasterio.open(p)
    return dataset.read(1)


def get_spatial_ref(p):
    dataset = rasterio.open(p)

    return dataset.transform, dataset.crs


def make_path(unit, i):
    """
​
    :return:
    """
    root = r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo\t2r_exports'
    root = r'C:\Users\mfichera\PycharmProjects\3D_mapping\ddmodeltest'
    return os.path.join(root, '{}_t2r{}.tif'.format(unit, i + 1))


def aggregate_surfaces(unit):
    n = 5
    container = None
    root = r'C:\Users\mfichera\PycharmProjects\3D_mapping\ddmodeltest'
    for i in range(n):
        p = make_path(unit, i)
        p = os.path.join(root, 'test_t2r{}.tif'.format(i + 1))
        surf = get_surface(p)
        print(surf)
        # stack surfaces into with container surface

        if container is None:
            container = surf
            transform, crs = get_spatial_ref(p)
            continue
        else:
            container = dstack((container, surf))
    # print(container)
    # print(container.mean(axis=2))
    # print(container.std(axis=2))
    # print(transform, crs)
    for name, data in (('mean_{}_{}'.format(unit, n), container.mean(axis=2)), ('std_{}_{}'.format(unit, n), container.std(axis=2))):
        out = r'C:\Users\mfichera\PycharmProjects\3D_mapping\ddmodeltest\{}.tif'.format(name)
        with rasterio.open(out, 'w', driver='GTiff', height=container.shape[0], width=container.shape[1],
                        count=1, dtype=container.dtype, transform=transform) as dst:
            dst.write(data, 1)


def main():
    units = ['alvb', 'udb', 'srt', 'ldb', 'dlb', 'uob', 'lob', 'artb']

    for unit in units:
        aggregate_surfaces(unit)


if __name__ == '__main__':
    main()
