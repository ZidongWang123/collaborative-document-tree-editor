import os
from lxml import etree
from comman_utils.Enums import Occurs
from comman_utils.Decorators import update_users
from ElementClass import Element


class DocTree:
    def __init__(self, templfile, importfile=None):
        self.name = "Unnamed"
        self.templates = self.create_templates(templfile["elements"])
        self.users = {}
        self.searched_element = None
        self.root = Element(templfile["root"], self, 0)

    @update_users(function_name="setDocumentName")
    def setName(self, name):
        self.name = name

    def getElementById(self, id):
        self.search_element(id=id)
        if self.searched_element:
            return self.searched_element
        else:
            return None

    def getElementByPath(self, path):
        path_array = path.split("/")
        path_array.reverse()
        self.search_element(path_array=path_array)
        if self.searched_element:
            return self.searched_element.getXML()
        return None

    def deleteElement(self, id):
        self.search_element(id=id)
        if self.searched_element:
            parent = self.searched_element.parent
            if parent:
                index = 0
                for child in parent.children:
                    if child == self.searched_element:
                        parent.removeChild(index)
                        break
                    index += 1

    def attach(self, user):
        if user not in self.users:
            self.users[user] = user.callback

    def detach(self, user):
        if user in self.users:
            del self.users[user]

    def export(self, exptype, directory, filename):
        if exptype != "html":
            print("export type is not supported")
            return
        
        html_root = etree.Element("html")
        head = etree.SubElement(html_root, "head")
        title = etree.SubElement(head, "title")
        title.text = self.name
        body = etree.SubElement(html_root, "body")

        xml_str = self.root.getXML()
        try:
            xml_element = etree.fromstring(xml_str.encode("utf-8"))
            body.append(xml_element)
        except Exception as e:
            print("Error parsing XML:", e)
            return

        html_str = etree.tostring(html_root, pretty_print=True).decode("utf-8")

        if not os.path.exists(directory):
            os.makedirs(directory)

        filename = filename + ".html" if filename else self.name + ".html"
        filepath = os.path.join(directory, filename)

        with open(filepath, "w") as f:
            f.write(html_str)

    def search_element(self, id=None, path_array=None):
        self.searched_element = None
        
        def id_search(element):
            if element.id == id:
                self.searched_element = element

        def path_search(element):
            current_element = element
            is_correct_path = True
            for item in path_array:
                if current_element is None or current_element.name != item:
                    is_correct_path = False
                    break
                current_element = current_element.parent
            if is_correct_path:
                self.searched_element = element
        
        if id:
            self.root.traverse(id_search)
        elif path_array:
            self.root.traverse(path_search)

    def create_templates(self, elements):
        templates = {}
        for key in elements:
            templates[key] = self.Template(elements[key].get("attrs", {}),
                                           elements[key].get("children", []),
                                           elements[key].get("occurs", "0"))
        for key in templates:
            templates[key].convert_children(templates)
        return templates

    class Template:
        def __init__(self, attrs, children, occurs):
            self.attrs = attrs
            self.children = children
            self.hasTextualContent = "text" in children
            self.occurs = Occurs.from_str(occurs)

        def convert_children(self, templates):
            children_dict = {}
            for child in self.children:
                if child != "text":
                    children_dict[child] = templates.get(child, None)
            self.children = children_dict
