from owslib import fes
from owslib.fes import SortBy, SortProperty
from owslib.csw import CatalogueServiceWeb
from geolinks import sniff_link

# CREDITS:
# code derived from:
# https://github.com/ioos/notebooks_demos/blob/master/notebooks/2016-12-19-exploring_csw.ipynb


def fes_date_filter(start, stop, constraint="overlaps"):
    """
    Take datetime-like objects and returns a fes filter for date range
    (begin and end inclusive).
    NOTE: Truncates the minutes!!!

    Examples
    --------
    >>> from datetime import datetime, timedelta
    >>> stop = datetime(2010, 1, 1, 12, 30, 59).replace(tzinfo=pytz.utc)
    >>> start = stop - timedelta(days=7)
    >>> begin, end = fes_date_filter(start, stop, constraint='overlaps')
    >>> begin.literal, end.literal
    ('2010-01-01 12:00', '2009-12-25 12:00')
    >>> begin.propertyoperator, end.propertyoperator
    ('ogc:PropertyIsLessThanOrEqualTo', 'ogc:PropertyIsGreaterThanOrEqualTo')
    >>> begin, end = fes_date_filter(start, stop, constraint='within')
    >>> begin.literal, end.literal
    ('2009-12-25 12:00', '2010-01-01 12:00')
    >>> begin.propertyoperator, end.propertyoperator
    ('ogc:PropertyIsGreaterThanOrEqualTo', 'ogc:PropertyIsLessThanOrEqualTo')

    """
    start = start.strftime("%Y-%m-%d %H:00")
    stop = stop.strftime("%Y-%m-%d %H:00")
    if constraint == "overlaps":
        propertyname = "apiso:TempExtent_begin"
        begin = fes.PropertyIsLessThanOrEqualTo(propertyname=propertyname, literal=stop)
        propertyname = "apiso:TempExtent_end"
        end = fes.PropertyIsGreaterThanOrEqualTo(
            propertyname=propertyname, literal=start
        )
    elif constraint == "within":
        propertyname = "apiso:TempExtent_begin"
        begin = fes.PropertyIsGreaterThanOrEqualTo(
            propertyname=propertyname, literal=start
        )
        propertyname = "apiso:TempExtent_end"
        end = fes.PropertyIsLessThanOrEqualTo(propertyname=propertyname, literal=stop)
    else:
        raise NameError("Unrecognized constraint {}".format(constraint))
    return begin, end


def get_csw_records(csw, filter_list, pagesize=10, maxrecords=1000):
    """Iterate `maxrecords`/`pagesize` times until the requested value in
    `maxrecords` is reached.
    """
    # Iterate over sorted results.
    sortby = SortBy([SortProperty("dc:title", "ASC")])
    csw_records = {}
    startposition = 0
    nextrecord = getattr(csw, "results", 1)
    while nextrecord != 0:
        csw.getrecords2(
            constraints=filter_list,
            startposition=startposition,
            maxrecords=pagesize,
            sortby=sortby,
        )
        csw_records.update(csw.records)
        if csw.results["nextrecord"] == 0:
            break
        startposition += pagesize + 1  # Last one is included.
        if startposition >= maxrecords:
            break
    csw.records.update(csw_records)


def csw_query(
    endpoint,
    bbox=None,
    start=None,
    stop=None,
    kw_names=None,
    crs="urn:ogc:def:crs:OGC:1.3:CRS84",
):
    constraints = []
    csw = None
    while csw is None:
        try:
            # connect
            csw = CatalogueServiceWeb(endpoint, timeout=60)
        except:
            pass
    if kw_names:
        kw = dict(
            wildCard="*", escapeChar="\\", singleChar="?", propertyname="apiso:AnyText"
        )
        or_filt = fes.Or(
            [fes.PropertyIsLike(literal=("*%s*" % val), **kw) for val in kw_names]
        )
        constraints.append(or_filt)

    if all(v is not None for v in [start, stop]):
        begin, end = fes_date_filter(start, stop)
        constraints.append(begin)
        constraints.append(end)

    if bbox:
        bbox_crs = fes.BBox(bbox, crs=crs)
        constraints.append(bbox_crs)
    if len(constraints) >= 2:
        filter_list = [fes.And(constraints)]
    else:
        filter_list = constraints
    get_csw_records(csw, filter_list, pagesize=10, maxrecords=1000)

    output = ""
    print("Found {} records.\n".format(len(csw.records.keys())))
    output += "Found {} records.\n".format(len(csw.records.keys()))

    for key, value in list(csw.records.items()):
        print("Title: [{}]\nID: {}\n".format(value.title, key))
        output += "\n"
        output += "Title: [{}]\nID: {}\n".format(value.title, key)
        msg = "geolink: {geolink}\nscheme: {scheme}\nURL: {url}\n".format
        for ref in value.references:
            output += "\n"
            print(msg(geolink=sniff_link(ref["url"]), **ref))
            output += msg(geolink=sniff_link(ref["url"]), **ref)
        print("#########################################################", "\n")
        output += "\n"
        output += "#########################################################"
        output += "\n"
    return output
