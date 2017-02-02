import properties

# Return True File is fine
# Return False File is not in valid content type
def mimetypeFilter(content_type):
	filtered = True
	for allowed_type in properties.ALLOWED_CONTENT_TYPE_FOR_IMAGES:
		if (allowed_type == content_type):
			filtered &= False
	return not filtered
