#!/usr/bin/env python3
import argparse
import datetime
import uuid
import pickle
import os
from fuzzywuzzy import fuzz

script_dir = os.path.dirname(os.path.realpath(__file__))
class TodoItem:
    def __init__(self, description, priority='z', project=None):
        self.uuid = str(uuid.uuid4())
        self.description = description
        self.priority = priority
        self.project = project if project else self.extract_project(description)
        self.created_time = datetime.datetime.now()
        self.completed_time = None

    @staticmethod
    def extract_project(description):
        # Extract the project name from the first word of the description
        return description.split()[0]

    def complete(self):
        # Mark the todo item as completed and set the completed time
        self.completed_time = datetime.datetime.now()

    def __str__(self):
        priority_str = f"({self.priority.upper()}) " if self.priority != 'z' else ""
        color_code = self.get_priority_color()
        reset_color_code = '\033[0m'
        return f"{color_code}{priority_str}+{self.project} {self.description}{reset_color_code}"

    def get_priority_color(self):
        if self.priority == 'a':
            return '\033[1m\033[93m'  # Yellow color for priority 'a'
        elif self.priority == 'b':
            return '\033[1m\033[92m'  # Green color for priority 'b'
        elif self.priority == 'c':
            return '\033[1m\033[94m'  # Blue color for priority 'c'
        elif self.priority == 'z':
            return ''  # No formatting for priority 'z'
        else:
            return '\033[1m'  # Bold for priority 'd' onwards

class Todo:
    def __init__(self, todos_file):
        self.todos_file = todos_file
        self.completed_file = todos_file.replace('todos.pkl', 'completed.pkl')
        self.todo_items = self.load_todo_items()
        self.completed_items = self.load_completed_items()

    def complete(self, index):
        if 1 <= index <= len(self.todo_items):
            completed_item = self.todo_items.pop(index - 1)  # Remove todo item from the list
            completed_item.complete()  # Mark the todo item as complete
            self.completed_items.append(completed_item)  # Add it to the completed list
            self.save_todo_items()  # Save todo items
            self.save_completed_items()  # Save completed items as well
            completion_time = completed_item.completed_time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"Todo item '{completed_item.description}' completed at {completion_time}")
            return True
        else:
            print("Invalid index. Please provide a valid index.")
            return False

    def append(self, item_number, text):
        index = item_number - 1
        if 0 <= index < len(self.todo_items):
            todo_item = self.todo_items[index]
            todo_item.description += " " + text
            self.save_todo_items()
            print(f"{todo_item.get_priority_color()}{item_number}. {todo_item}")
            return True
        else:
            print("Invalid item number. Please provide a valid item number.")
            return False

    def prepend(self, item_number, text):
        index = item_number - 1
        if 0 <= index < len(self.todo_items):
            todo_item = self.todo_items[index]
            todo_item.description = text + " " + todo_item.description
            self.save_todo_items()
            print(f"{todo_item.get_priority_color()}{item_number}. {todo_item}")
            return True
        else:
            print("Invalid item number. Please provide a valid item number.")
            return False

    def delete(self, index):
        if 1 <= index <= len(self.todo_items):
            deleted_item = self.todo_items.pop(index - 1)  # Remove todo item from the list
            self.save_todo_items()  # Save todo items
            print(f"Todo item '{deleted_item.description}' deleted successfully.")
            return True
        else:
            print("Invalid index. Please provide a valid index.")
            return False

    def load_todo_items(self):
        try:
            with open(self.todos_file, 'rb') as file:
                todo_items = pickle.load(file)
                return sorted(todo_items, key=lambda x: (x.priority, x.project, x.description))
        except FileNotFoundError:
            return []

    def save_todo_items(self):
        with open(self.todos_file, 'wb') as file:
            pickle.dump(self.todo_items, file)

    def load_completed_items(self):
        try:
            with open(self.completed_file, 'rb') as file:
                completed_items = pickle.load(file)
                return completed_items
        except FileNotFoundError:
            return []

    def save_completed_items(self):
        with open(self.completed_file, 'wb') as file:
            pickle.dump(self.completed_items, file)

    def add_todo_item(self, description, priority='z', project=None):
        # Check if +word exists in description and extract project
        project_indicator_index = description.find("+")
        if project_indicator_index != -1:
            space_after_indicator_index = description.find(" ", project_indicator_index)
            if space_after_indicator_index == -1:  # Check if +word is at the end of the sentence
                project = description[project_indicator_index + 1:].strip()
                description = description.replace("+" + project, "").strip()
            else:
                project = description[project_indicator_index + 1:space_after_indicator_index]
                description = description.replace("+" + project, "").strip()

        # Check if @a to @z exists in description and extract priority
        priority_indicator_index = description.find("@")
        if priority_indicator_index != -1:
            priority_char = description[priority_indicator_index + 1]
            if priority_char.isalpha() and priority_char.lower() in "abcdefghijklmnopqrstuvwxyz":
                # Check if the priority indicator is followed by a space or it is at the end of the sentence
                if (priority_indicator_index + 2 < len(description) and 
                        description[priority_indicator_index + 2] == " ") or (priority_indicator_index == len(description) - 2):
                    priority = priority_char.lower()
                    description = description.replace("@" + priority, "").strip()

        todo_item = TodoItem(description, priority, project)
        self.todo_items.append(todo_item)
        self.todo_items.sort(key=lambda x: (x.priority, x.project, x.description))  # Sort the list
        self.save_todo_items()

    def report(self):
        today = datetime.datetime.now()
        eight_days_ago = today - datetime.timedelta(days=8)

        # Filter completed items within the last 8 days
        recent_completed_items = [item for item in self.completed_items if item.completed_time >= eight_days_ago]

        # Sort the recent completed items by completion time
        sorted_recent_completed_items = sorted(recent_completed_items, key=lambda x: x.completed_time)

        # Print the report
        if sorted_recent_completed_items:
            print("Completed items in the last week:")
            for item in sorted_recent_completed_items:
                print(f"{item.completed_time.strftime('%Y-%m-%d %H:%M:%S')}: {item.description}")
        else:
            print("No completed items in the last week")

    def list_fuzzy_match(self, query):
        matched_items = []

        for i, item in enumerate(self.todo_items):
            if fuzz.partial_ratio(item.project, query) >= 90:
                matched_items.append((i, item))

        for i, item in enumerate(self.todo_items):
            if fuzz.partial_ratio(item.description, query) >= 70:  # Adjust the threshold as needed
                matched_items.append((i, item))

        if matched_items:
            for index, item in matched_items:
                print(f"{item.get_priority_color()}{index + 1}. {item}")
        else:
            print("No items found.")

    def set_priority(self, index, priority):
        if 1 <= index <= len(self.todo_items):
            item = self.todo_items[index - 1]
            item.priority = priority
            self.todo_items.sort(key=lambda x: (x.priority, x.project, x.description))  # Sort the list
            self.save_todo_items()
            self.print()
            return True
        else:
            print("Invalid index. Please provide a valid index.")
            return False

    def __str__(self):
        formatted_items = [f"{todo_item.get_priority_color()}{index+1}. {todo_item}" for index, todo_item in enumerate(self.todo_items)]
        return '\n'.join(formatted_items)

    def print(self):
        print(self)

def parse_args():
    parser = argparse.ArgumentParser(description="Manage todos")
    subparsers = parser.add_subparsers(dest="command")

    # Add subcommand
    add_parser = subparsers.add_parser("add", aliases=["a"], help="Add a todo")
    add_parser.add_argument("todo", nargs="+", help="Todo description")

    # List subcommand
    list_parser = subparsers.add_parser("list", aliases=["l"], help="List todos")
    list_parser.add_argument("search", nargs="*", help="Optional search query for fuzzy search")

    # Priority subcommand
    pri_parser = subparsers.add_parser("pri", aliases=["p"], help="Set priority for a todo")
    pri_parser.add_argument("item_number", type=int, help="Todo item number")
    pri_parser.add_argument("priority", choices=[chr(i) for i in range(ord('a'), ord('z')+1)], help="Priority level (a-z)")

    # Done subcommand
    done_parser = subparsers.add_parser("done", aliases=["d"], help="Mark todo as done")
    done_parser.add_argument("item_number", type=int, help="Todo item number")

    # Delete subcommand
    parser_delete = subparsers.add_parser("delete", aliases=["del"], help="Delete a todo item")
    parser_delete.add_argument("item_number", type=int, help="Todo item number")

    # Report command
    parser_report = subparsers.add_parser("report", aliases=["r"], help="Generate a report of completed items")

    prep_parser = subparsers.add_parser("prep", help="Prepend text to a todo item")
    prep_parser.add_argument("item_number", type=int, help="Todo item number")
    prep_parser.add_argument("text", nargs="+", help="Text to prepend to the todo item")

    # Append subcommand
    app_parser = subparsers.add_parser("app", help="Append text to a todo item")
    app_parser.add_argument("item_number", type=int, help="Todo item number")
    app_parser.add_argument("text", nargs="+", help="Text to append to the todo item")    

    return parser.parse_args()

def main():
    args = parse_args()


    todos_file = os.path.join(script_dir, "todos.pkl")
    todo_list = Todo(todos_file)

    if args.command in {"add", "a"}:
        todo_list.add_todo_item(" ".join(args.todo))
        todo_list.print()
    elif args.command in {"list", "l"}:
        if args.search:
            todo_list.list_fuzzy_match(" ".join(args.search))
        else:
            todo_list.print()
    elif args.command in {"pri", "p"}:
        todo_list.set_priority(args.item_number, args.priority)
    elif args.command in {"done", "d"}:
        todo_list.complete(args.item_number)
    elif args.command in {"delete", "del"}:
        todo_list.delete(args.item_number)
    elif args.command in {"report", "r"}:
        todo_list.report()
    elif args.command == "app":
        todo_list.append(args.item_number, " ".join(args.text))
    elif args.command == "prep":
        todo_list.prepend(args.item_number, " ".join(args.text))
    else:
        todo_list.print()

if __name__ == "__main__":
    main()

