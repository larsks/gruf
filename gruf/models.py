import json


class Model (object):
    streaming = False

    def __init__(self, stdout):
        self.stdout = stdout
        self.decode_response()


class Approval(dict):
    def __str__(self):
        try:
            return '<{type} for {patch[ref]} by {by[username]} {description} {value}>'.format(**self)  # NOQA
        except KeyError:
            return '<{type} for {patch[ref]} by {by[username]}>'.format(**self)  # NOQA


class Patch(dict):
    def __iter__(self):
        return iter(self.approvals)

    @property
    def approvals(self):
        for approval in self.get('approvals', []):
            yield Approval(patch=self, **approval)

    def __str__(self):
        return '<Patch {ref}>'.format(**self)


class Change(dict):
    def __init__(self, **kwargs):
        self.update(kwargs)

    def __iter__(self):
        return iter(self.patches)

    @property
    def patches(self):
        for patch in self.get('patchSets', []):
            yield Patch(**patch)

    def __str__(self):
        return '<Change {number}>'.format(**self)


class QueryResponse (Model):
    def __iter__(self):
        return iter(self.changes)

    def decode_response(self):
        self.changes = [Change(**line) for line in (
            json.loads(line) for line in self.stdout)
            if line.get('type') != 'stats']


class ProjectListResponse (Model):
    def __iter__(self):
        return (dict(name=k, **v) for k, v in self.projects.items())

    def decode_response(self):
        self.projects = json.loads('\n'.join(line for line in self.stdout))


class UnstructuredResponse (Model):
    def __iter__(self):
        return iter(self.response)

    def decode_response(self):
        self.response = [line for line in self.stdout]

    def __str__(self):
        return '\n'.join(self.response)


class MemberListResponse (Model):
    fields = ('id', 'username', 'fullname', 'email')

    def __iter__(self):
        return iter(self.members)

    def decode_response(self):
        self.members = [
            dict(zip(self.fields, line.split('\t')))
            for line in self.stdout]


class GroupListResponse (Model):
    fields = ('name', 'uuid', 'description', 'owner_name',
              'owner_uuid', 'public')

    def __iter__(self):
        return iter(self.groups)

    def decode_response(self):
        self.groups = [
            dict(zip(self.fields, line.split('\t')))
            for line in self.stdout]


class EventStream (Model):
    streaming = True

    def decode_response(self):
        pass

    def __iter__(self):
        return self.events

    @property
    def events(self):
        for line in self.stdout:
            yield json.loads(line)
