import netCDF4 as nc
from netCDF4 import num2date


def get_datetimes_from_source(src_file):
    src = nc.Dataset(src_file)
    data = nc.num2date(src["time"][:], src["time"].units)
    src.close()
    return data


def create_file_from_source(src_file, trg_file, time_indexes=slice(None)):
    src = nc.Dataset(src_file)
    trg = nc.Dataset(trg_file, mode="w")

    # Create the dimensions of the file
    for name, dim in src.dimensions.items():
        dim_length = len(dim)
        if name == "time":
            dim_length = len(time_indexes)
        trg.createDimension(name, dim_length if not dim.isunlimited() else None)

    # Copy the global attributes
    trg.setncatts({a: src.getncattr(a) for a in src.ncattrs()})

    # Create the variables in the file
    for name, var in src.variables.items():
        trg.createVariable(name, var.dtype, var.dimensions)

        # Copy the variable attributes
        trg.variables[name].setncatts({a: var.getncattr(a) for a in var.ncattrs()})

        # Copy the variables values (as 'f4' eventually)
        data = src.variables[name][:]

        if name in ("time", "values", "Mesh2D_s1"):
            data = data[time_indexes]

        trg.variables[name][:] = data

    # Save the file
    trg.close()
    src.close()
