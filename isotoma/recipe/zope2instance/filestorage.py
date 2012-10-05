# -*- coding: utf-8 -*-
"""Recipe filestorage"""

"""
This is a temporary fork of collective.recipe.filestorage 0.6 to stop implicit dependency creation
"""

import os

from zc.buildout import UserError

class Filestorage(object):
    """zc.buildout recipe"""

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        active_parts = [p.strip() for p in self.buildout['buildout']['parts'].split()]
        
        # figure out which ZEO we're going to inject filestorage configuration into, if any
        zeo_address = None
        self.zeo_part = options.get('zeo', None)
        if self.zeo_part is not None:
            if self.buildout.has_key(self.zeo_part):
                zeo_address = self.buildout[self.zeo_part].get('zeo-address', 8100)
            else:
                raise UserError, '[isotoma.recipe.zope2instance:filestorage] "%s" part specifies nonexistant zeo part "%s".' % (name, self.zeo_part)
        else:
            for part_name in active_parts:
                part = self.buildout._raw[part_name]
                if not part.has_key('recipe'):
                    continue
                elif part['recipe'] in ('plone.recipe.zope2zeoserver', 'plone.recipe.zeoserver'):
                    if self.zeo_part is not None:
                        raise UserError, '[isotoma.recipe.zope2instance:filestorage] "%s" part found multiple zeoserver parts; please specify which one to use with the "zeo" option.' % name
                    self.zeo_part = part_name
                    zeo_address = part.get('zeo-address', 8100)
                
        # figure out which Zopes we're going to inject filestorage configuration into
        self.zope_parts = options.get('zopes', '').split()
        if len(self.zope_parts) == 0:
            for part_name in active_parts:
                part = self.buildout._raw[part_name]
                if not part.has_key('recipe'):
                    continue
                elif part['recipe'] in ('plone.recipe.zope2instance', 'isotoma.recipe.zope2instance'):
                    if zeo_address is None or zeo_address == part.get('zeo-address', 8100):
                        self.zope_parts.append(part_name)
                
    def install(self):
        # inject the extra sections into the correct zope-conf-additional or zeo-conf-additional variables.
        self.subparts = options.get('parts', '').split()
        for subpart in self.subparts:
            for zope_part in self.zope_parts:
                self._inject_zope_conf(zope_part, subpart)
            if self.zeo_part is not None:
                self._inject_zeo_conf(self.zeo_part, subpart)

       
        for subpart in self.subparts:
            # create the directory for this filestorage
            location = self._subpart_option(subpart, 'location', default=os.path.join('var', 'filestorage', '%(fs_part_name)s', '%(fs_part_name)s.fs'))
            location = os.path.join(self.buildout['buildout']['directory'], location)
            fs_dir = os.path.dirname(location)
            if not os.path.exists(fs_dir):
                os.makedirs(fs_dir)
            
            # create blobstorage dirs
            blob_storage = os.path.join('var', 'blobstorage-%(fs_part_name)s')
            if self._subpart_option(subpart, 'blob-storage', default=''):
                blob_storage = self._subpart_option(subpart, 'blob-storage', default=blob_storage)
                if not blob_storage.startswith(os.path.sep):
                    blob_storage = os.path.join(self.buildout['buildout']['directory'], blob_storage)
                if not os.path.exists(blob_storage):
                    os.makedirs(blob_storage)
            
                if self.zeo_part:
                    zeo_blob_storage = self._subpart_option(subpart, 'zeo-blob-storage', default=blob_storage)
                    if not zeo_blob_storage.startswith(os.path.sep):
                        zeo_blob_storage = os.path.join(self.buildout['buildout']['directory'], zeo_blob_storage)
                    if not os.path.exists(zeo_blob_storage):
                        os.makedirs(zeo_blob_storage)

        # return an empty list because we don't have anything we want buildout to automatically remove
        return tuple()

    def update(self):
        """Updater"""
        pass
        
    def _inject_zope_conf(self, zope_part, subpart):
        zope_options = self.buildout[zope_part]
        
        location = self._subpart_option(subpart, 'location', default=os.path.join('var', 'filestorage', '%(fs_part_name)s', '%(fs_part_name)s.fs'))
        location = os.path.join(self.buildout['buildout']['directory'], location)
        
        storage_template = file_storage_template
        blob_storage = os.path.join('var', 'blobstorage-%(fs_part_name)s')
        blob_enabled = False
        if self._subpart_option(subpart, 'blob-storage', default=''):
            blob_enabled = True
            blob_storage = self._subpart_option(subpart, 'blob-storage', default=blob_storage)
            if not blob_storage.startswith(os.path.sep):
                blob_storage = os.path.join(self.buildout['buildout']['directory'], blob_storage)
            storage_template = self._blob_storage_template(zope_part)
        storage_snippet = storage_template % dict(
            fs_name = '',
            fs_path = location,
            blob_storage = blob_storage,
            )
        
        if zope_options.get('zeo-client', 'false').lower() in ('yes', 'true', 'on', '1'):
            zeo_address = self._subpart_option(subpart, 'zeo-address', default='8100', inherit=(zope_part, self.zeo_part))
            zeo_client_cache_size = self._subpart_option(subpart, 'zeo-client-cache-size', default='30MB', inherit=zope_part)
            zeo_client_client = self._subpart_option(subpart, 'zeo-client-client', default='', inherit=zope_part)
            if zeo_client_client:
                zeo_client_client = 'client %s' % zeo_client_client
            zeo_storage = self._subpart_option(subpart, 'zeo-storage', default='%(fs_part_name)s')
            zeo_client_name = self._subpart_option(subpart, 'zeo-client-name', default='%(fs_part_name)s_zeostorage')
            zeo_client_var = self._subpart_option(subpart, 'zeo-client-var', default=os.path.join(zope_options['location'], 'var'))
            
            zeo_storage_template = zeo_file_storage_template
            zeo_blob_storage = self._subpart_option(subpart, 'zeo-blob-storage', default=blob_storage)
            if not zeo_blob_storage.startswith(os.path.sep):
                zeo_blob_storage = os.path.join(self.buildout['buildout']['directory'], zeo_blob_storage)
            zeo_shared_blob_dir = self._subpart_option(subpart, 'zeo-shared-blob-dir', default='on')
            if blob_enabled:
                zeo_storage_template = zeo_blob_storage_template
            
            storage_snippet = zeo_storage_template % dict(
                zeo_address = zeo_address,
                zeo_client_cache_size = zeo_client_cache_size,
                zeo_client_client = zeo_client_client,
                zeo_storage = zeo_storage,
                zeo_client_name = zeo_client_name,
                zeo_client_var=zeo_client_var,
                zeo_blob_storage = zeo_blob_storage,
                zeo_shared_blob_dir = zeo_shared_blob_dir,
                )
        
        zodb_cache_size = self._subpart_option(subpart, 'zodb-cache-size', default='5000', inherit=zope_part)
        zodb_name = self._subpart_option(subpart, 'zodb-name', default='%(fs_part_name)s')
        zodb_mountpoint = self._subpart_option(subpart, 'zodb-mountpoint', default='/%(fs_part_name)s')
        zodb_container_class = self._subpart_option(subpart, 'zodb-container-class', default='')
        if zodb_container_class:
            zodb_container_class = "\n    container-class %s" % zodb_container_class
        zodb_stanza = zodb_template % dict(
            zodb_name = zodb_name,
            zodb_mountpoint = zodb_mountpoint,
            zodb_container_class = zodb_container_class,
            zodb_cache_size = zodb_cache_size,
            storage_snippet = storage_snippet.strip()
            )
            
        zope_conf_additional = zope_options.get('zope-conf-additional', '')
        zope_options['zope-conf-additional'] = zope_conf_additional + zodb_stanza
    
    def _inject_zeo_conf(self, zeo_part, subpart):
        zeo_options = self.buildout[zeo_part]
        
        location = self._subpart_option(subpart, 'location', default=os.path.join('var', 'filestorage', '%(fs_part_name)s', '%(fs_part_name)s.fs'))
        location = os.path.join(self.buildout['buildout']['directory'], location)
        zeo_storage = self._subpart_option(subpart, 'zeo-storage', default='%(fs_part_name)s')
        
        storage_template = file_storage_template
        blob_storage = os.path.join('var', 'blobstorage-%(fs_part_name)s')
        if self._subpart_option(subpart, 'blob-storage', default=''):
            blob_storage = self._subpart_option(subpart, 'blob-storage', default=blob_storage)
            if not blob_storage.startswith(os.path.sep):
                blob_storage = os.path.join(self.buildout['buildout']['directory'], blob_storage)
            storage_template = self._blob_storage_template(zeo_part)
        
        storage_snippet = storage_template % dict(
            fs_name=zeo_storage,
            fs_path=location,
            blob_storage=blob_storage,
            )

        zeo_conf_additional = zeo_options.get('zeo-conf-additional', '')
        zeo_options['zeo-conf-additional'] = zeo_conf_additional + storage_snippet
    
    def _subpart_option(self, subpart, option, default=None, inherit=()):
        """ Retrieve an option for a filestorage subpart, perhaps falling back to other specified parts.
            Also substitutes the name of the subpart. 
        """
        
        parts_to_check = ['filestorage_' + subpart, self.name]
        if type(inherit) == type(''):
            inherit = (inherit,)
        parts_to_check.extend(inherit)
        
        val = default
        for part in parts_to_check:
            if not self.buildout.has_key(part):
                continue
            if self.buildout[part].has_key(option):
                val = self.buildout[part][option]
                break
        
        return val % dict(
            fs_part_name = subpart
            )
    
    def _blob_storage_template(self, part):
        if self.buildout[part].has_key('zope2-location'):
            # non-eggified Zope; assume ZODB 3.8.x
            return blob_storage_zodb_3_8_template
        else:
            return blob_storage_zodb_3_9_template
    
# Storage snippets for zope.conf template
file_storage_template="""
    <filestorage %(fs_name)s>
      path %(fs_path)s
    </filestorage>
"""

blob_storage_zodb_3_8_template="""
    <blobstorage %(fs_name)s>
      blob-dir %(blob_storage)s
      <filestorage %(fs_name)s>
        path %(fs_path)s
      </filestorage>
    </blobstorage>
"""

blob_storage_zodb_3_9_template="""
    <filestorage %(fs_name)s>
      path %(fs_path)s
      blob-dir %(blob_storage)s
    </filestorage>
"""

zeo_file_storage_template="""
    <zeoclient>
      server %(zeo_address)s
      storage %(zeo_storage)s
      name %(zeo_client_name)s
      var %(zeo_client_var)s
      cache-size %(zeo_client_cache_size)s
      %(zeo_client_client)s
    </zeoclient>
""".strip()

zeo_blob_storage_template="""
    <zeoclient>
      blob-dir %(zeo_blob_storage)s
      shared-blob-dir %(zeo_shared_blob_dir)s
      server %(zeo_address)s
      storage %(zeo_storage)s
      name %(zeo_client_name)s
      var %(zeo_client_var)s
      cache-size %(zeo_client_cache_size)s
      %(zeo_client_client)s
    </zeoclient>
""".strip()

zodb_template="""
<zodb_db %(zodb_name)s>
    cache-size %(zodb_cache_size)s
    %(storage_snippet)s
    mount-point %(zodb_mountpoint)s%(zodb_container_class)s
</zodb_db>
"""
