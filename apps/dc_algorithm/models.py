# Copyright 2016 United States Government as represented by the Administrator
# of the National Aeronautics and Space Administration. All Rights Reserved.
#
# Portion of this code is Copyright Geoscience Australia, Licensed under the
# Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License
# at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# The CEOS 2 platform is licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.db import models
from django.core.exceptions import ValidationError

import datetime
import uuid


class Satellite(models.Model):
    """Stores a satellite that exists in the Data Cube

    Stores a single instance of a Satellite object that contains all the information for
    Data Cube requests. This is both used to create Data Cube queries and to display forms
    on the UI.

    Attributes:
        satellite_id: This should correspond with a Data Cube platform.
            e.g. LANDSAT_5, LANDSAT_7, SENTINEL_1A, etc.
        satellite_name: Used to display forms to users
            e.g. Landsat 5, Landsat 7, Sentinel-1A
        product_prefix: In our Data Cube setup, we use product prefixes combined with an area.
            e.g. ls5_ledaps_{vietnam,colombia,australia}, s1a_gamma0_vietnam
            This should be the 'ls5_ledaps_' and 's1a_gamma0_' part of the above examples.
            You should be able to concat the product prefix and an area id to get a valid dataset query.
        date_min and date_max: Satellite valid data date range.
            e.g. If you have LS7 data from 2000-2016, you should use that as the date range.

    """

    satellite_id = models.CharField(max_length=25, unique=True)
    satellite_name = models.CharField(max_length=25)
    product_prefix = models.CharField(max_length=25)

    date_min = models.DateField('date_min', default=datetime.date.today)
    date_max = models.DateField('date_min', default=datetime.date.today)

    def __str__(self):
        return self.satellite_id


class Area(models.Model):
    """Stores an area corresponding to an area that has been ingested into the Data Cube.

    Areas define geographic regions that exist in a Data Cube. Attributes define the geographic range,
    imagery to use for the map view, and the satellites that we have acquired data for over the area.

    Attributes:
        area_id: This should correspond with a Data Cube product. The area id is combined
            with a satellite id to create a product id used to query the Data Cube for data.
            e.g. colombia, vietnam, australia will be used to create ls5_ledaps_colombia etc.
        area_name: Human readable name for the area
        latitude/longitude min/max: These bounds define the valid data region in the Data Cube.
            e.g. enter the bounds generated by get_datacube_metadata - this is used to create an outline on the map
            highlighting valid data.
        main_imagery: Path to an image to use as the globe imagery - it should be relatively high resolution if its a real image.
            The image at the entered path will be overlaid on the globe from [-180,180] longitude and [-90, 90] latitude.
            Defaults to black.png which is just a black background for the entire globe.
        detail_imagery: Path to an image to use as the base for our valid data region. This should be as close to the latitude/longitude
            min/max bounds as possible.
        thumbnail_imagery: path to an image to be used as a small icon on the region selection page.
        detail latitude/longitude min/max: These bounds should correspond to the actual bounds of the detail imagery. This is used to overlay
            the detail imagery on the globe just in case your detail image doesn't exactly match up with the valid data region.
        satellites: M2M field describing the satellites that we have data for over any given region. Only select satellites that the Data Cube
            has data ingested for - e.g. if we only have S1 over vietnam, we would leave colombia and australia unchecked.

    """

    area_id = models.CharField(max_length=250, default="", unique=True)
    area_name = models.CharField(max_length=250, default="")

    latitude_min = models.FloatField(default=0)
    latitude_max = models.FloatField(default=0)
    longitude_min = models.FloatField(default=0)
    longitude_max = models.FloatField(default=0)

    main_imagery = models.CharField(max_length=250, default="/static/assets/images/black.png")
    detail_imagery = models.CharField(max_length=250, default="")
    thumbnail_imagery = models.CharField(max_length=250, default="")

    detail_latitude_min = models.FloatField(default=0)
    detail_latitude_max = models.FloatField(default=0)
    detail_longitude_min = models.FloatField(default=0)
    detail_longitude_max = models.FloatField(default=0)

    satellites = models.ManyToManyField(Satellite)

    def __str__(self):
        return self.area_id


class Application(models.Model):
    """Model containing the applications that are displayed on the UI.

    The Application model is used to control application attributes. An example of an application
    could be:
        NDVI: Computes the NDVI over any given region.
        Water Detection: Generates water detection images over a given region
        etc.

    This model is used in templates to create dropdown menus/route users to different apps.

    Attributes:
        application_id: Unique id used to identify apps.
        application_name: Human readable name for the app. Will be featured on UI pages.
        areas: M2M field outlining what areas should be displayed for each app. If we have an inland
            area with no standing water bodies, then we may not want to display water detection here
            so we would leave it unselected.
        satellites: M2M field outlining what satellties should be displayed for each tool. If water detection
            does not use SAR data, we would select only optical satellites here.
        color_scale: path to a color scale image to be displayed in the main tool view. If no color scale is
            necessary, this should be left blank/null.

    """

    application_id = models.CharField(max_length=250, default="", unique=True)
    application_name = models.CharField(max_length=250, default="")
    areas = models.ManyToManyField(Area)
    satellites = models.ManyToManyField(Satellite)

    color_scale = models.CharField(max_length=250, default="", blank=True, null=True)

    def __str__(self):
        return self.application_id


class ToolInfo(models.Model):
    """Model used to handle the region selection page information and images.

    Stores images and information for the region selection page for each tool. Information includes
    the descriptions seen on the page as well as their respective images. For instance, if we want
    three images to scroll across the carousel, we would create three ToolInfo instances each with
    an image and description.

    Attributes:
        image_path: path to the banner image that is to be shown on the top of the page
        image_title: title describing the image - will be displayed on page.
        image_description: description text for the image. Will be displayed on page.

    """

    image_path = models.CharField(max_length=100)
    image_title = models.CharField(max_length=50)
    image_description = models.CharField(max_length=500)

    application = models.ForeignKey(Application)


class Compositor(models.Model):
    """
    Stores a compositor including a human readable name and an id.
    The id is interpretted in each app.
    These are used to populate UI forms.
    """

    compositor_id = models.CharField(max_length=25, unique=True)
    compositor_name = models.CharField(max_length=25)


class Baseline(models.Model):
    """
    stores a baseline type. E.g. mean, composite, etc. Used for change
    detection applications.
    """

    baseline_id = models.CharField(max_length=25, unique=True)
    baseline_name = models.CharField(max_length=25)


class AnimationType(models.Model):
    """
    Stores a single instance of an animation type. Includes human readable, id, variable and band.
    These correspond to the datatypes and bands found in tasks.py for the animation enabled apps.
    Used to populate UI forms.
    Band number and data variable are interpretted at the app level in tasks.py.
    """
    type_id = models.CharField(max_length=25, default="None", unique=True)
    app_name = models.CharField(max_length=25, default="None")
    type_name = models.CharField(max_length=25, default="None")
    data_variable = models.CharField(max_length=25, default="None")
    band_number = models.CharField(max_length=25, default="None")


##############################################################################################################
# Begin base classes for apps - Query, metadata, results, result types. Extends only in the case of app
# specific elements.
##############################################################################################################


class Query(models.Model):
    """Base Query model meant to be inherited by a TaskClass

    Serves as the base of all algorithm query, containing some basic metadata
    such as title, description, and self timing functionality.

    Additionally, basic time, latitude, and longitude ranges are provided
    along with platform/product used for querying the Data Cube.

    Constraints:
        All fields excluding primary key are unique together.
        No fields are optional - defaults are provided only in specific fields

    Usage:
        In each app, subclass Query and add all fields (if desired).
        Subclass Meta and add the newly added fields (if any) to the list of
        unique_together fields in the meta class. e.g.
            class AppQuery(Query):
                sample_field = models.CharField(max_length=100)

                class Meta(Query.Meta):
                    unique_together = (('platform', 'product', 'time_start', 'time_end', 'latitude_max', 'latitude_min',
                                        'longitude_max', 'longitude_min', 'sample_field'))


    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=10000)

    query_start = models.DateTimeField('query_start', default=datetime.datetime.now)
    query_end = models.DateTimeField('query_end', default=datetime.datetime.now)

    area_id = models.CharField(max_length=100)

    platform = models.CharField(max_length=25)
    product = models.CharField(max_length=50)

    time_start = models.DateField('time_start')
    time_end = models.DateField('time_end')
    latitude_min = models.FloatField()
    latitude_max = models.FloatField()
    longitude_min = models.FloatField()
    longitude_max = models.FloatField()

    #false by default, only change is false-> true
    complete = models.BooleanField(default=False)

    class Meta:
        abstract = True
        unique_together = (('platform', 'product', 'time_start', 'time_end', 'latitude_max', 'latitude_min',
                            'longitude_max', 'longitude_min'))

    @classmethod
    def get_queryset_from_history(cls, user_history, **kwargs):
        """Get a QuerySet of Query objects using the a user history queryset

        User history is defined in this class and must contain task_id and should be filtered already.
        The list of task ids are generated and used in a filter function on Query. Kwargs are passed directly
        in to the query filter function as kwargs.

        Args:
            user_history: Pre filtered UserHistory queryset - must contain attr task_id
            **kwargs: Any valid queryset key word arguments - common uses include complete=False, etc.

        Returns:
            Queryset of queries that fit the criteria and belong to the user.

        """
        queryset_pks = [user_history_entry.task_id for user_history_entry in user_history]
        return cls.objects.filter(pk__in=queryset_pks, **kwargs)

    @classmethod
    def get_or_create_query_from_post(cls, form_data):
        """Get or create a query obj from post form data

        Using a python dict formatted with post_data_to_dict, form a set of query parameters.
        Any formatting of parameters should be done here - including strings to datetime.datetime,
        list to strings, etc. The dict is then filtered for 'valid fields' by comparing it to
        a list of fields on this model. The query is saved in a try catch - if there is a validation error
        then the query exists and should be grabbed with 'get'.

        Args:
            form_data: python dict containing either a single obj or a list formatted with post_data_to_dict

        Returns:
            Tuple containing the query model and a boolean value signifying if it was created or loaded.

        """
        """
        def get_or_create_query_from_post(cls, form_data):
            query_data = form_data
            query_data['time_start'] = datetime.datetime.strptime(form_data['time_start'], '%m/%d/%Y')
            query_data['time_end'] = datetime.datetime.strptime(form_data['time_end'], '%m/%d/%Y')

            query_data['product'] = Satellite.objects.get(
                satellite_id=query_data['platform']).product_prefix + Area.objects.get(
                    area_id=query_data['area_id']).area_id
            query_data['title'] = "Base Query" if 'title' not in form_data or form_data['title'] == '' else form_data[
                'title']
            query_data['description'] = "None" if 'description' not in form_data or form_data[
                'description'] == '' else form_data['description']

            valid_query_fields = [field.name for field in cls._meta.get_fields()]
            query_data = {key: query_data[key] for key in valid_query_fields if key in query_data}
            query = cls(**query_data)

            try:
                query = cls.objects.get(**query_data)
                return query, False
            except cls.DoesNotExist:
                query = cls(**query_data)
                query.save()
                return query, True
        """
        raise NotImplementedError(
            "You must define the classmethod 'get_or_create_query_from_post' in the inheriting class.")


class Metadata(models.Model):
    """Base Metadata model meant to be inherited by a TaskClass

    Serves as the base of all algorithm metadata, containing basic fields such as scene
    count, pixel count, clean pixel statistics. Comma seperated fields are also used here
    and zipped/fetched using the get_field_as_list function.

    Constraints:
        All fields excluding primary key are unique together.
        all fields are optional and will be replaced with valid values when they
            are generated by the task.

    Usage:
        In each app, subclass Metadata and add all fields (if desired).
        Subclass Meta as well to ensure the class remains abstract e.g.
            class AppMetadata(Metadata):
                sample_field = models.CharField(max_length=100)

                class Meta(Metadata.Meta):
                    pass

    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)

    #meta attributes
    scene_count = models.IntegerField(default=0)
    pixel_count = models.IntegerField(default=0)
    clean_pixel_count = models.IntegerField(default=0)
    percentage_clean_pixels = models.FloatField(default=0)
    # comma seperated dates representing individual acquisitions
    # followed by comma seperated numbers representing pixels per scene.
    acquisition_list = models.CharField(max_length=100000, default="")
    clean_pixels_per_acquisition = models.CharField(max_length=100000, default="")
    clean_pixel_percentages_per_acquisition = models.CharField(max_length=100000, default="")

    #more to come?

    class Meta:
        abstract = True

    def _get_field_as_list(self, field_name):
        """Convert comma seperated strings into lists

        Certain metadata fields are stored as comma seperated lists of properties.
        Use this function to get the string, split on comma, and return the result.

        Args:
            field_name: field name as a string that should be converted

        Returns:
            List of attributes
        """

        return getattr(self, field_name).rstrip(',').split(',')

    def get_zipped_fields_as_list(self, fields):
        """Creates a zipped iterable comprised of all the fields

        Using _get_field_as_list converts the comma seperated fields in fields
        and zips them to iterate. Used to display grouped metadata, generally by
        acquisition date.

        Args:
            fields: iterable of comma seperated fields that should be grouped.

        Returns:
            zipped iterable containing grouped fields generated using _get_field_as_list
        """

        return zip(self._get_field_as_list(field) for field in fields)


class Result(models.Model):
    """Base Result model meant to be inherited by a TaskClass

    Serves as the base of all algorithm resluts, containing a status, number of scenes
    processed and total scenes (to generate progress bar), and a result path.
    The result path is required and is the path to the result that should be the
    *Default* result shown on the UI map. Other results can be added in subclasses.

    Constraints:
        result_path is required and must lead to an image that serves as the default result
            to be displayed to the user.

    Usage:
        In each app, subclass Result and add all fields (if desired).
        Subclass Meta as well to ensure the class remains abstract e.g.
            class AppResult(Result):
                sample_field = models.CharField(max_length=100)

                class Meta(Result.Meta):
                    pass

    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)

    #either OK or ERROR or WAIT
    status = models.CharField(max_length=100, default="")
    #used to pass messages to the user. 
    message = models.CharField(max_length=100, default="")

    scenes_processed = models.IntegerField(default=0)
    total_scenes = models.IntegerField(default=0)
    #default display result.
    result_path = models.CharField(max_length=250, default="")

    class Meta:
        abstract = True

    def get_progress(self):
        """Quantify the progress of a result's processing in terms of its own attributes

        Meant to return a representation of progress based on attributes set in a task.
        Should be overwritten in the task if scenes processed and total scenes aren't
        a useful representation

        Returns:
            An integer between 0 and 100

        """
        total_scenes = self.total_scenes if self.total_scenes > 0 else 1
        percent_complete = self.scenes_processed / total_scenes
        rounded_int = round(percent_complete * 100)
        clamped_int = max(0, min(rounded_int, 100))
        return


class GenericTask(Query, Metadata, Result):
    """Serves as the model for an algorithm task containing a Query, Metadata, and Result

    The generic task should be implemented by each application. Each app should subclass
    Query, Result, and Metadata, adding all desired fields according to docstrings. The
    app should then include a AppTask implementation that ties them all together:
        CustomMosaicTask(CustomMosaicQuery, CustomMosaicMetadata, CustomMosaicResult):
            pass

    This Generic task should not be subclassed and should be used only as a model for how
    things should be tied together at the app level.

    Constraints:
        Should subclass Query, Metadata, and Result (or a subclass of each)
        Should be used for all processing and be passed using a uuid pk
        Attributes should NOT be added to this class - add them to the inherited classes

    """

    pass

    class Meta:
        abstract = True


class ResultType(models.Model):
    """Stores a result type for an app that relates to options in the celery tasks

    Contains a satellite id, result id, and result type for differentiating between different
    result types. the result type should be displayed on the UI, passing the result_id as form data.
    The result_id should be handled directly in the celery task execution. This should be inherited at the
    app level without inheriting meta - the resulting class should not be abstract.

    Constraints:
        None yet.

    """

    satellite_id = models.CharField(max_length=25)
    result_id = models.CharField(max_length=25)
    result_name = models.CharField(max_length=25)

    class Meta:
        abstract = True


class UserHistory(models.Model):
    """Contains the task history for a given user.

    This shoud act as a linking table between a user and their tasks.
    When a new task is submitted, a row should be created linking the user
    to the task by id.

    Constraints:
        user_id should map to a user's id.
        task_id should map to the pk of a task

    """

    user_id = models.IntegerField()
    task_id = models.UUIDField()

    class Meta:
        abstract = True
